from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
import schemas
from auth_utils import get_current_user
from database import get_db
from routes.utils import (
    apply_fraud_analysis,
    serialize_customer,
    serialize_device,
    serialize_merchant,
    serialize_transaction,
)

router = APIRouter()


@router.get("/", response_model=List[schemas.TransactionOut])
def list_transactions(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    risk_category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Transaction)

    if risk_category and risk_category != "all":
        try:
            query = query.filter(models.Transaction.risk_category == models.RiskCategory(risk_category))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid risk category.")

    if search:
        query = query.filter(
            or_(
                models.Transaction.transaction_id.contains(search),
                models.Transaction.location.contains(search),
                models.Transaction.sender_id.contains(search),
            )
        )

    transactions = query.order_by(models.Transaction.timestamp.desc()).offset(skip).limit(limit).all()
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/reference")
def reference_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return {
        "customers": [serialize_customer(customer) for customer in db.query(models.Customer).order_by(models.Customer.name).all()],
        "merchants": [serialize_merchant(merchant) for merchant in db.query(models.Merchant).order_by(models.Merchant.name).all()],
        "devices": [serialize_device(device) for device in db.query(models.Device).order_by(models.Device.device_type).all()],
        "transaction_types": [item.value for item in models.TransactionType],
    }


@router.post("/", response_model=schemas.FraudAnalysisResult, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    sender = db.query(models.Customer).filter(models.Customer.id == payload.sender_id).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender customer not found.")

    if not payload.receiver_id and not payload.merchant_id:
        raise HTTPException(status_code=422, detail="Provide either a receiver or a merchant.")

    if payload.receiver_id:
        receiver = db.query(models.Customer).filter(models.Customer.id == payload.receiver_id).first()
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver customer not found.")
        if payload.receiver_id == payload.sender_id:
            raise HTTPException(status_code=422, detail="Sender and receiver cannot be the same customer.")

    if payload.merchant_id and not db.query(models.Merchant).filter(models.Merchant.id == payload.merchant_id).first():
        raise HTTPException(status_code=404, detail="Merchant not found.")

    if payload.device_id and not db.query(models.Device).filter(models.Device.id == payload.device_id).first():
        raise HTTPException(status_code=404, detail="Device not found.")

    transaction = models.Transaction(
        sender_id=payload.sender_id,
        receiver_id=payload.receiver_id,
        merchant_id=payload.merchant_id,
        device_id=payload.device_id,
        amount=payload.amount,
        currency=payload.currency,
        location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        transaction_type=payload.transaction_type,
        status=models.TransactionStatus.pending,
    )
    db.add(transaction)
    db.flush()

    result, alert = apply_fraud_analysis(transaction, db)
    db.commit()
    db.refresh(transaction)

    return schemas.FraudAnalysisResult(
        transaction_id=transaction.transaction_id,
        risk_score=result["overall_score"],
        risk_category=result["risk_category"],
        fraud_label=result["fraud_label"],
        fraud_reasons=result["fraud_reasons"],
        rule_score=result["rule_score"],
        ml_score=result["ml_score"],
        graph_score=result["graph_score"],
        flags=result["flags"],
        explanation=result["explanation"],
        alert_created=alert is not None,
        alert_id=alert.id if alert else None,
    )


@router.get("/{transaction_id}", response_model=schemas.TransactionDetail)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transaction = (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    detail = serialize_transaction(transaction)
    detail["sender"] = serialize_customer(transaction.sender) if transaction.sender else None
    detail["merchant"] = serialize_merchant(transaction.merchant) if transaction.merchant else None
    detail["device"] = serialize_device(transaction.device) if transaction.device else None
    return detail
