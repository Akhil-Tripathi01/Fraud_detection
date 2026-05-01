"""
Fraud Detection Engine
Hybrid scoring: Rule-based + ML Anomaly Detection + Graph Pattern Analysis.
Assigns a risk score (0–100) and categorizes each transaction.
"""

import json
import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session
import models

logger = logging.getLogger(__name__)

# ─── Thresholds & Configuration ───────────────────────────────────────────────
HIGH_AMOUNT_THRESHOLD    = 50_000    # INR — flag transactions above this
VELOCITY_TIME_WINDOW     = 60        # minutes — check for rapid transactions
VELOCITY_MAX_COUNT       = 5         # max transactions in window before flag
VELOCITY_MAX_AMOUNT      = 1_00_000  # max cumulative amount in window
LOCATION_DISTANCE_KM     = 500       # flag if location changes more than this
UNUSUAL_HOURS_START      = 0         # midnight
UNUSUAL_HOURS_END        = 5         # 5 AM
DEVICE_SHARING_THRESHOLD = 3         # flag device used by more than N customers


# ─── Helper Functions ─────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers."""
    R = 6371  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def risk_category(score: float) -> str:
    if score <= 30:
        return "low"
    elif score <= 70:
        return "medium"
    return "high"


# ─── Rule-Based Checks ────────────────────────────────────────────────────────

def check_high_amount(transaction: models.Transaction) -> Tuple[bool, float, str]:
    """Flag unusually large transactions."""
    if transaction.amount >= HIGH_AMOUNT_THRESHOLD:
        extra = min((transaction.amount - HIGH_AMOUNT_THRESHOLD) / HIGH_AMOUNT_THRESHOLD, 1.0)
        score = 25 + extra * 20
        return True, score, f"High amount: INR {transaction.amount:,.0f} exceeds threshold INR {HIGH_AMOUNT_THRESHOLD:,}"
    return False, 0.0, ""


def check_velocity(transaction: models.Transaction, db: Session) -> Tuple[bool, float, str]:
    """Flag rapid transaction sequences from same sender."""
    window_start = datetime.utcnow() - timedelta(minutes=VELOCITY_TIME_WINDOW)
    recent = db.query(models.Transaction).filter(
        models.Transaction.sender_id == transaction.sender_id,
        models.Transaction.timestamp >= window_start,
        models.Transaction.transaction_id != transaction.transaction_id,
    ).all()

    count = len(recent)
    total_amount = sum(t.amount for t in recent) + transaction.amount

    if count >= VELOCITY_MAX_COUNT or total_amount >= VELOCITY_MAX_AMOUNT:
        score = min(20 + count * 4, 35)
        return True, score, (
            f"Velocity alert: {count + 1} transactions in {VELOCITY_TIME_WINDOW}min, "
            f"total INR {total_amount:,.0f}"
        )
    return False, 0.0, ""


def check_device_sharing(transaction: models.Transaction, db: Session) -> Tuple[bool, float, str]:
    """Flag devices used by multiple distinct customers."""
    if not transaction.device_id:
        return False, 0.0, ""

    unique_users = (
        db.query(models.Transaction.sender_id)
        .filter(
            models.Transaction.device_id == transaction.device_id,
            models.Transaction.transaction_id != transaction.transaction_id,
        )
        .distinct()
        .count()
    )

    if unique_users >= DEVICE_SHARING_THRESHOLD:
        score = min(15 + unique_users * 5, 30)
        return True, score, f"Device shared by {unique_users + 1} different customers"
    return False, 0.0, ""


def check_location_anomaly(transaction: models.Transaction, db: Session) -> Tuple[bool, float, str]:
    """Flag sudden geographic jumps between consecutive transactions."""
    if not (transaction.latitude and transaction.longitude):
        return False, 0.0, ""

    prev = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.sender_id == transaction.sender_id,
            models.Transaction.transaction_id != transaction.transaction_id,
            models.Transaction.latitude.isnot(None),
        )
        .order_by(models.Transaction.timestamp.desc())
        .first()
    )

    if prev and prev.latitude and prev.longitude:
        dist = haversine_distance(prev.latitude, prev.longitude, transaction.latitude, transaction.longitude)
        if dist > LOCATION_DISTANCE_KM:
            score = min(10 + dist / 100, 25)
            return True, score, f"Location anomaly: {dist:.0f} km jump from last transaction"
    return False, 0.0, ""


def check_unusual_hours(transaction: models.Transaction) -> Tuple[bool, float, str]:
    """Flag transactions during suspicious hours (midnight–5 AM)."""
    hour = transaction.timestamp.hour if transaction.timestamp else datetime.utcnow().hour
    if UNUSUAL_HOURS_START <= hour < UNUSUAL_HOURS_END:
        return True, 10.0, f"Unusual hour: transaction at {hour:02d}:00"
    return False, 0.0, ""


def check_new_merchant(transaction: models.Transaction, db: Session) -> Tuple[bool, float, str]:
    """Flag first-time transactions with a merchant."""
    if not transaction.merchant_id:
        return False, 0.0, ""

    prev_count = db.query(models.Transaction).filter(
        models.Transaction.sender_id == transaction.sender_id,
        models.Transaction.merchant_id == transaction.merchant_id,
        models.Transaction.transaction_id != transaction.transaction_id,
    ).count()

    if prev_count == 0:
        return True, 5.0, "First transaction with this merchant"
    return False, 0.0, ""


def check_flagged_merchant(transaction: models.Transaction, db: Session) -> Tuple[bool, float, str]:
    """Flag transactions with known suspicious merchants."""
    if not transaction.merchant_id:
        return False, 0.0, ""
    merchant = db.query(models.Merchant).filter(models.Merchant.id == transaction.merchant_id).first()
    if merchant and merchant.is_flagged:
        return True, 20.0, f"Merchant '{merchant.name}' is flagged as suspicious"
    return False, 0.0, ""


def check_flagged_customer(transaction: models.Transaction, db: Session) -> Tuple[bool, float, str]:
    """Flag transactions involving a flagged customer."""
    sender = db.query(models.Customer).filter(models.Customer.id == transaction.sender_id).first()
    if sender and sender.is_flagged:
        return True, 20.0, f"Sender account '{sender.name}' is flagged"
    return False, 0.0, ""


# ─── ML Anomaly Score (Placeholder) ──────────────────────────────────────────

def ml_anomaly_score(transaction: models.Transaction, db: Session) -> float:
    """
    Placeholder ML anomaly scoring.
    In a real system, this would call a trained Isolation Forest,
    Autoencoder, or PyTorch Geometric GNN model.
    Here we simulate realistic scoring based on statistical features.
    """
    # Feature 1: Amount deviation (simulated z-score)
    sender_txns = db.query(models.Transaction).filter(
        models.Transaction.sender_id == transaction.sender_id
    ).all()

    if len(sender_txns) > 2:
        amounts = [t.amount for t in sender_txns]
        mean_amt = sum(amounts) / len(amounts)
        std_amt = (sum((a - mean_amt) ** 2 for a in amounts) / len(amounts)) ** 0.5
        z_score = abs(transaction.amount - mean_amt) / (std_amt + 1)
        amount_anomaly = min(z_score * 8, 40)
    else:
        amount_anomaly = random.uniform(5, 15)  # cold start

    # Feature 2: Hour-of-day anomaly
    hour = transaction.timestamp.hour if transaction.timestamp else 12
    # Normal peak: 9–21. Off-peak gets higher anomaly.
    hour_anomaly = max(0, (abs(hour - 15) - 6) * 2.5)

    # Feature 3: Transaction type risk weight
    type_weights = {
        "transfer": 10, "withdrawal": 15, "purchase": 5,
        "payment": 5, "deposit": 2, "refund": 20
    }
    type_anomaly = type_weights.get(str(transaction.transaction_type).split(".")[-1], 5)

    ml_score = (amount_anomaly * 0.6 + hour_anomaly * 0.2 + type_anomaly * 0.2)
    return round(min(ml_score, 40), 2)


# ─── Graph-Based Pattern Score ────────────────────────────────────────────────

def graph_pattern_score(transaction: models.Transaction, db: Session) -> Tuple[float, bool]:
    """
    Detect fraud ring / network patterns using graph topology.
    Returns (score, ring_detected).
    """
    if not transaction.receiver_id:
        return 0.0, False

    # Pattern: Multiple senders → same receiver (hub pattern)
    receiver_senders = (
        db.query(models.Transaction.sender_id)
        .filter(
            models.Transaction.receiver_id == transaction.receiver_id,
            models.Transaction.transaction_id != transaction.transaction_id,
        )
        .distinct()
        .count()
    )

    # Pattern: Same sender → many receivers in short time (fan-out)
    window = datetime.utcnow() - timedelta(hours=24)
    sender_receivers = (
        db.query(models.Transaction.receiver_id)
        .filter(
            models.Transaction.sender_id == transaction.sender_id,
            models.Transaction.timestamp >= window,
        )
        .distinct()
        .count()
    )

    ring_detected = receiver_senders >= 4 or sender_receivers >= 6
    score = min(receiver_senders * 4 + sender_receivers * 3, 30)

    return round(score, 2), ring_detected


# ─── Master Fraud Scoring Engine ──────────────────────────────────────────────

def analyze_transaction(transaction: models.Transaction, db: Session) -> Dict[str, Any]:
    """
    Run the complete hybrid fraud analysis on a transaction.
    Returns a structured result dict with score, flags, and explanations.
    """
    reasons: List[str] = []
    rule_score = 0.0

    flags = {
        "high_amount_flag":       False,
        "velocity_flag":          False,
        "device_sharing_flag":    False,
        "location_anomaly_flag":  False,
        "ring_pattern_flag":      False,
        "unusual_hours_flag":     False,
        "new_merchant_flag":      False,
    }

    # ── Rule Checks ──────────────────────────────────────────────────────────
    checks = [
        ("high_amount_flag",      check_high_amount(transaction)),
        ("velocity_flag",         check_velocity(transaction, db)),
        ("device_sharing_flag",   check_device_sharing(transaction, db)),
        ("location_anomaly_flag", check_location_anomaly(transaction, db)),
        ("unusual_hours_flag",    check_unusual_hours(transaction)),
        ("new_merchant_flag",     check_new_merchant(transaction, db)),
    ]

    # Extra checks (no dedicated flag)
    flagged_merchant = check_flagged_merchant(transaction, db)
    flagged_customer = check_flagged_customer(transaction, db)

    for flag_key, (triggered, score, reason) in checks:
        if triggered:
            flags[flag_key] = True
            rule_score += score
            reasons.append(reason)

    for triggered, score, reason in [flagged_merchant, flagged_customer]:
        if triggered:
            rule_score += score
            reasons.append(reason)

    rule_score = min(rule_score, 60)

    # ── ML Score ─────────────────────────────────────────────────────────────
    ml_score = ml_anomaly_score(transaction, db)

    # ── Graph Score ───────────────────────────────────────────────────────────
    graph_score, ring_detected = graph_pattern_score(transaction, db)
    if ring_detected:
        flags["ring_pattern_flag"] = True
        reasons.append("Potential fraud ring: hub/spoke transaction pattern detected")

    # ── Final Combined Score ─────────────────────────────────────────────────
    # Weighted normalized combination. Component ranges are intentionally
    # different (rules: 0-60, ML: 0-40, graph: 0-30), so normalize before
    # applying the documented 50/30/20 blend.
    overall = (
        (rule_score / 60 * 50 if rule_score else 0)
        + (ml_score / 40 * 30 if ml_score else 0)
        + (graph_score / 30 * 20 if graph_score else 0)
    )

    # Boost: if multiple flags triggered, increase score
    active_flags = sum(1 for v in flags.values() if v)
    if active_flags >= 4:
        overall = min(overall * 1.5, 100)
    elif active_flags >= 3:
        overall = min(overall * 1.35, 100)

    overall = round(min(overall, 100), 2)
    category = risk_category(overall)
    is_fraud = overall >= 71

    # ── Human-Readable Explanation ────────────────────────────────────────────
    if not reasons:
        explanation = "No suspicious patterns detected. Transaction appears normal."
    else:
        explanation = f"Suspicious activity: {len(reasons)} pattern(s) detected: " + "; ".join(reasons[:3])
        if len(reasons) > 3:
            explanation += f" (+{len(reasons) - 3} more)"

    return {
        "overall_score":           overall,
        "risk_category":           category,
        "fraud_label":             is_fraud,
        "fraud_reasons":           reasons,
        "rule_score":              round(rule_score, 2),
        "ml_score":                round(ml_score, 2),
        "graph_score":             round(graph_score, 2),
        "flags":                   flags,
        "explanation":             explanation,
        "active_flag_count":       active_flags,
    }


def determine_alert_type(flags: Dict[str, bool], reasons: List[str]) -> str:
    """Determine the primary alert type based on triggered flags."""
    if flags.get("ring_pattern_flag"):
        return "fraud_ring"
    if flags.get("device_sharing_flag"):
        return "device_sharing"
    if flags.get("velocity_flag"):
        return "velocity_abuse"
    if flags.get("location_anomaly_flag"):
        return "location_anomaly"
    if flags.get("high_amount_flag"):
        return "high_value"
    if flags.get("unusual_hours_flag"):
        return "unusual_hours"
    return "general_suspicious"


def determine_severity(score: float) -> str:
    if score >= 85:
        return "critical"
    elif score >= 70:
        return "high"
    elif score >= 50:
        return "medium"
    return "low"
