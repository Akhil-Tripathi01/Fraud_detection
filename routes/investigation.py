from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from auth_utils import get_current_user
from database import get_db
from routes.utils import serialize_alert, serialize_risk_score, serialize_transaction

router = APIRouter()


def investigation_detail(alert: models.FraudAlert) -> dict:
    transaction = alert.transaction
    return {
        "alert": serialize_alert(alert),
        "transaction": serialize_transaction(transaction) if transaction else None,
        "notes": alert.notes,
        "risk_score": serialize_risk_score(transaction.risk_record) if transaction and transaction.risk_record else None,
    }


@router.get("/cases", response_model=List[schemas.InvestigationDetail])
def list_cases(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.FraudAlert)
    if status and status != "all":
        query = query.filter(models.FraudAlert.status == models.AlertStatus(status))
    alerts = query.order_by(models.FraudAlert.created_at.desc()).all()
    return [investigation_detail(alert) for alert in alerts]


@router.get("/cases/{alert_id}", response_model=schemas.InvestigationDetail)
def get_case(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alert = db.query(models.FraudAlert).filter(models.FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Investigation case not found.")
    return investigation_detail(alert)


@router.post("/notes", response_model=schemas.NoteOut)
def add_note(
    payload: schemas.NoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alert = db.query(models.FraudAlert).filter(models.FraudAlert.id == payload.alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    note = models.InvestigationNote(
        alert_id=payload.alert_id,
        investigator_id=current_user.id,
        note_text=payload.note_text,
        action_taken=payload.action_taken,
    )
    db.add(note)
    if alert.status == models.AlertStatus.open:
        alert.status = models.AlertStatus.investigating
    db.commit()
    db.refresh(note)
    return note


@router.patch("/cases/{alert_id}/status", response_model=schemas.AlertOut)
def update_case_status(
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
