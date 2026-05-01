from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from auth_utils import get_current_user
from database import get_db
from routes.utils import apply_fraud_analysis, serialize_alert, serialize_risk_score

router = APIRouter()


@router.get("/alerts", response_model=List[schemas.AlertOut])
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.FraudAlert)
    if status and status != "all":
        query = query.filter(models.FraudAlert.status == models.AlertStatus(status))
    if severity and severity != "all":
        query = query.filter(models.FraudAlert.severity == models.AlertSeverity(severity))
    alerts = query.order_by(models.FraudAlert.created_at.desc()).limit(limit).all()
    return [serialize_alert(alert) for alert in alerts]


@router.get("/alerts/{alert_id}", response_model=schemas.AlertOut)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alert = db.query(models.FraudAlert).filter(models.FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return serialize_alert(alert)


@router.patch("/alerts/{alert_id}", response_model=schemas.AlertOut)
def update_alert(
    alert_id: str,
    payload: schemas.AlertUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alert = db.query(models.FraudAlert).filter(models.FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.status = payload.status
    if payload.status in {models.AlertStatus.resolved, models.AlertStatus.false_positive}:
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = current_user.id
    else:
        alert.resolved_at = None
        alert.resolved_by = None

    if payload.note:
        db.add(
            models.InvestigationNote(
                alert_id=alert.id,
                investigator_id=current_user.id,
                note_text=payload.note,
                action_taken=f"status:{payload.status.value}",
            )
        )

    db.commit()
    db.refresh(alert)
    return serialize_alert(alert)


@router.get("/risk-scores", response_model=List[schemas.RiskScoreOut])
def list_risk_scores(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    risks = db.query(models.RiskScore).order_by(models.RiskScore.analyzed_at.desc()).limit(limit).all()
    return [serialize_risk_score(risk) for risk in risks]


@router.post("/analyze/{transaction_id}", response_model=schemas.FraudAnalysisResult)
def analyze_existing_transaction(
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

    result, alert = apply_fraud_analysis(transaction, db)
    db.commit()

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
