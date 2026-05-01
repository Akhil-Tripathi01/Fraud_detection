from collections import Counter, defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from auth_utils import get_current_user
from database import get_db

router = APIRouter()


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transactions = db.query(models.Transaction).all()
    alerts = db.query(models.FraudAlert).all()

    return {
        "total_transactions": len(transactions),
        "total_alerts": len(alerts),
        "high_risk_count": sum(1 for tx in transactions if tx.risk_category == models.RiskCategory.high),
        "medium_risk_count": sum(1 for tx in transactions if tx.risk_category == models.RiskCategory.medium),
        "low_risk_count": sum(1 for tx in transactions if tx.risk_category == models.RiskCategory.low),
        "open_alerts": sum(1 for alert in alerts if alert.status == models.AlertStatus.open),
        "resolved_alerts": sum(1 for alert in alerts if alert.status == models.AlertStatus.resolved),
        "fraud_rate_percent": round(
            (sum(1 for tx in transactions if tx.fraud_label) / len(transactions) * 100) if transactions else 0,
            2,
        ),
        "total_flagged_amount": round(sum(tx.amount for tx in transactions if tx.risk_score >= 50), 2),
        "total_customers": db.query(models.Customer).count(),
        "total_merchants": db.query(models.Merchant).count(),
    }


@router.get("/stats", response_model=schemas.DashboardStats)
def stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transactions = db.query(models.Transaction).all()
    alerts = db.query(models.FraudAlert).all()
    today = datetime.utcnow().date()

    volume_by_day = defaultdict(lambda: {"count": 0, "amount": 0.0})
    risk_by_day = defaultdict(lambda: {"low": 0, "medium": 0, "high": 0})
    for tx in transactions:
        tx_date = (tx.timestamp or datetime.utcnow()).date()
        key = tx_date.isoformat()
        volume_by_day[key]["count"] += 1
        volume_by_day[key]["amount"] += tx.amount
        risk_by_day[key][tx.risk_category.value] += 1

    daily_transaction_volume = []
    risk_trend = []
    for offset in range(13, -1, -1):
        key = (today - timedelta(days=offset)).isoformat()
        daily_transaction_volume.append(
            {
                "date": key,
                "count": volume_by_day[key]["count"],
                "amount": round(volume_by_day[key]["amount"], 2),
            }
        )
        risk_trend.append({"date": key, **risk_by_day[key]})

    flagged_customers = (
        db.query(models.Customer)
        .order_by(models.Customer.risk_score.desc())
        .limit(5)
        .all()
    )
    top_flagged_customers = [
        {
            "id": customer.id,
            "name": customer.name,
            "risk_score": round(customer.risk_score or 0, 2),
            "city": customer.city,
            "is_flagged": customer.is_flagged,
        }
        for customer in flagged_customers
    ]

    flagged_merchants = (
        db.query(models.Merchant)
        .order_by(models.Merchant.is_flagged.desc(), models.Merchant.total_transactions.desc())
        .limit(5)
        .all()
    )
    top_flagged_merchants = [
        {
            "id": merchant.id,
            "name": merchant.name,
            "category": merchant.category,
            "risk_level": merchant.risk_level,
            "is_flagged": merchant.is_flagged,
            "transactions": merchant.total_transactions,
        }
        for merchant in flagged_merchants
    ]

    alert_type_distribution = dict(Counter(alert.alert_type for alert in alerts if alert.alert_type))

    return {
        "daily_transaction_volume": daily_transaction_volume,
        "risk_trend": risk_trend,
        "top_flagged_customers": top_flagged_customers,
        "top_flagged_merchants": top_flagged_merchants,
        "alert_type_distribution": alert_type_distribution,
    }


@router.get("/risk-distribution", response_model=schemas.RiskDistribution)
def risk_distribution(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    transactions = db.query(models.Transaction).all()
    low = sum(1 for tx in transactions if tx.risk_category == models.RiskCategory.low)
    medium = sum(1 for tx in transactions if tx.risk_category == models.RiskCategory.medium)
    high = sum(1 for tx in transactions if tx.risk_category == models.RiskCategory.high)
    total = len(transactions)
    return {
        "low": low,
        "medium": medium,
        "high": high,
        "total": total,
        "low_percent": round(low / total * 100, 2) if total else 0,
        "medium_percent": round(medium / total * 100, 2) if total else 0,
        "high_percent": round(high / total * 100, 2) if total else 0,
    }
