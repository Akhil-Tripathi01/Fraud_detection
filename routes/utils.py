"""Shared route helpers for serialization and fraud analysis persistence."""

import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

import models
from fraud_engine import analyze_transaction, determine_alert_type, determine_severity


def enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def serialize_customer(customer: models.Customer) -> Dict[str, Any]:
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "account_number": customer.account_number,
        "account_type": customer.account_type,
        "balance": customer.balance,
        "city": customer.city,
        "country": customer.country,
        "is_flagged": customer.is_flagged,
        "risk_score": customer.risk_score,
        "created_at": customer.created_at,
    }


def serialize_merchant(merchant: models.Merchant) -> Dict[str, Any]:
    return {
        "id": merchant.id,
        "name": merchant.name,
        "category": merchant.category,
        "location": merchant.location,
        "country": merchant.country,
        "is_flagged": merchant.is_flagged,
        "risk_level": merchant.risk_level,
        "total_transactions": merchant.total_transactions,
        "created_at": merchant.created_at,
    }


def serialize_device(device: models.Device) -> Dict[str, Any]:
    return {
        "id": device.id,
        "device_hash": device.device_hash,
        "device_type": device.device_type,
        "os": device.os,
        "browser": device.browser,
        "ip_address": device.ip_address,
        "is_flagged": device.is_flagged,
        "created_at": device.created_at,
    }


def serialize_transaction(transaction: models.Transaction) -> Dict[str, Any]:
    return {
        "transaction_id": transaction.transaction_id,
        "sender_id": transaction.sender_id,
        "receiver_id": transaction.receiver_id,
        "merchant_id": transaction.merchant_id,
        "device_id": transaction.device_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "location": transaction.location,
        "transaction_type": enum_value(transaction.transaction_type),
        "status": enum_value(transaction.status),
        "risk_score": transaction.risk_score,
        "risk_category": enum_value(transaction.risk_category),
        "fraud_label": transaction.fraud_label,
        "fraud_reasons": transaction.fraud_reasons,
        "timestamp": transaction.timestamp,
    }


def serialize_alert(alert: models.FraudAlert) -> Dict[str, Any]:
    return {
        "id": alert.id,
        "transaction_id": alert.transaction_id,
        "alert_type": alert.alert_type,
        "severity": enum_value(alert.severity),
        "status": enum_value(alert.status),
        "description": alert.description,
        "triggered_rules": alert.triggered_rules,
        "risk_score": alert.risk_score,
        "created_at": alert.created_at,
        "resolved_at": alert.resolved_at,
    }


def serialize_risk_score(risk: models.RiskScore) -> Dict[str, Any]:
    return {
        "transaction_id": risk.transaction_id,
        "overall_score": risk.overall_score,
        "risk_category": enum_value(risk_category_from_score(risk.overall_score)),
        "rule_score": risk.rule_score,
        "ml_score": risk.ml_score,
        "graph_score": risk.graph_score,
        "high_amount_flag": risk.high_amount_flag,
        "velocity_flag": risk.velocity_flag,
        "device_sharing_flag": risk.device_sharing_flag,
        "location_anomaly_flag": risk.location_anomaly_flag,
        "ring_pattern_flag": risk.ring_pattern_flag,
        "unusual_hours_flag": risk.unusual_hours_flag,
        "new_merchant_flag": risk.new_merchant_flag,
        "explanation": risk.explanation,
        "analyzed_at": risk.analyzed_at,
    }


def risk_category_from_score(score: Optional[float]) -> models.RiskCategory:
    value = score or 0
    if value <= 30:
        return models.RiskCategory.low
    if value <= 70:
        return models.RiskCategory.medium
    return models.RiskCategory.high


def parse_json_list(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else [str(value)]
    except json.JSONDecodeError:
        return [raw]


def apply_fraud_analysis(
    transaction: models.Transaction,
    db: Session,
    create_alert: bool = True,
) -> Tuple[Dict[str, Any], Optional[models.FraudAlert]]:
    result = analyze_transaction(transaction, db)
    category = models.RiskCategory(result["risk_category"])

    transaction.risk_score = result["overall_score"]
    transaction.risk_category = category
    transaction.fraud_label = result["fraud_label"]
    transaction.fraud_reasons = json.dumps(result["fraud_reasons"])
    transaction.status = (
        models.TransactionStatus.flagged
        if result["overall_score"] >= 70
        else models.TransactionStatus.completed
    )
    transaction.processed_at = datetime.utcnow()

    risk = (
        db.query(models.RiskScore)
        .filter(models.RiskScore.transaction_id == transaction.transaction_id)
        .first()
    )
    if not risk:
        risk = models.RiskScore(transaction_id=transaction.transaction_id)
        db.add(risk)

    flags = result["flags"]
    risk.overall_score = result["overall_score"]
    risk.rule_score = result["rule_score"]
    risk.ml_score = result["ml_score"]
    risk.graph_score = result["graph_score"]
    risk.high_amount_flag = flags["high_amount_flag"]
    risk.velocity_flag = flags["velocity_flag"]
    risk.device_sharing_flag = flags["device_sharing_flag"]
    risk.location_anomaly_flag = flags["location_anomaly_flag"]
    risk.ring_pattern_flag = flags["ring_pattern_flag"]
    risk.unusual_hours_flag = flags["unusual_hours_flag"]
    risk.new_merchant_flag = flags["new_merchant_flag"]
    risk.explanation = result["explanation"]
    risk.analyzed_at = datetime.utcnow()

    sender = db.query(models.Customer).filter(models.Customer.id == transaction.sender_id).first()
    if sender:
        sender.risk_score = max(sender.risk_score or 0, result["overall_score"])
        if result["overall_score"] >= 70:
            sender.is_flagged = True

    merchant = None
    if transaction.merchant_id:
        merchant = db.query(models.Merchant).filter(models.Merchant.id == transaction.merchant_id).first()
        if merchant:
            merchant.total_transactions = (
                db.query(models.Transaction)
                .filter(models.Transaction.merchant_id == transaction.merchant_id)
                .count()
            )
            if result["overall_score"] >= 70:
                merchant.risk_level = "high"

    alert = None
    if create_alert and result["overall_score"] >= 50:
        alert = (
            db.query(models.FraudAlert)
            .filter(models.FraudAlert.transaction_id == transaction.transaction_id)
            .first()
        )
        if not alert:
            alert = models.FraudAlert(
                transaction_id=transaction.transaction_id,
                status=models.AlertStatus.open,
            )
            db.add(alert)

        alert.alert_type = determine_alert_type(flags, result["fraud_reasons"])
        alert.severity = models.AlertSeverity(determine_severity(result["overall_score"]))
        alert.description = result["explanation"]
        alert.triggered_rules = json.dumps(result["fraud_reasons"])
        alert.risk_score = result["overall_score"]

    db.flush()
    return result, alert
