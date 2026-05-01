"""
Database Models (ORM)
All SQLAlchemy table definitions for the Fraud Detection Platform.
"""

from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid


def generate_uuid():
    return str(uuid.uuid4())


# ─── Enumerations ─────────────────────────────────────────────────────────────

class TransactionType(str, enum.Enum):
    transfer       = "transfer"
    payment        = "payment"
    withdrawal     = "withdrawal"
    deposit        = "deposit"
    purchase       = "purchase"
    refund         = "refund"


class TransactionStatus(str, enum.Enum):
    pending    = "pending"
    completed  = "completed"
    failed     = "failed"
    flagged    = "flagged"
    blocked    = "blocked"


class RiskCategory(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


class AlertStatus(str, enum.Enum):
    open         = "open"
    investigating = "investigating"
    resolved     = "resolved"
    false_positive = "false_positive"


class AlertSeverity(str, enum.Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    """Admin / investigator user accounts."""
    __tablename__ = "users"

    id         = Column(String, primary_key=True, default=generate_uuid)
    username   = Column(String(50), unique=True, nullable=False, index=True)
    email      = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name  = Column(String(100))
    role       = Column(String(20), default="investigator")  # admin | investigator | analyst
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    notes = relationship("InvestigationNote", back_populates="investigator")


class Customer(Base):
    """Bank customers (transaction senders/receivers)."""
    __tablename__ = "customers"

    id             = Column(String, primary_key=True, default=generate_uuid)
    name           = Column(String(100), nullable=False)
    email          = Column(String(100), unique=True, nullable=False, index=True)
    phone          = Column(String(20))
    account_number = Column(String(20), unique=True, nullable=False)
    account_type   = Column(String(20), default="savings")  # savings | current | business
    balance        = Column(Float, default=0.0)
    country        = Column(String(50), default="India")
    city           = Column(String(50))
    is_flagged     = Column(Boolean, default=False)
    risk_score     = Column(Float, default=0.0)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    sent_transactions     = relationship("Transaction", foreign_keys="Transaction.sender_id",     back_populates="sender")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.receiver_id",   back_populates="receiver")


class Merchant(Base):
    """Merchants involved in transactions."""
    __tablename__ = "merchants"

    id              = Column(String, primary_key=True, default=generate_uuid)
    name            = Column(String(100), nullable=False)
    category        = Column(String(50))  # retail, food, crypto, travel, etc.
    location        = Column(String(100))
    country         = Column(String(50), default="India")
    is_flagged      = Column(Boolean, default=False)
    risk_level      = Column(String(10), default="low")
    total_transactions = Column(Integer, default=0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="merchant")


class Device(Base):
    """Devices used for transactions (mobile, browser, ATM)."""
    __tablename__ = "devices"

    id           = Column(String, primary_key=True, default=generate_uuid)
    device_hash  = Column(String(64), unique=True, nullable=False)  # fingerprint
    device_type  = Column(String(20))   # mobile | desktop | atm | pos
    os           = Column(String(30))
    browser      = Column(String(30))
    ip_address   = Column(String(45))
    is_flagged   = Column(Boolean, default=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="device")


class Transaction(Base):
    """Core transaction record — the main graph edge."""
    __tablename__ = "transactions"

    transaction_id   = Column(String, primary_key=True, default=generate_uuid)
    sender_id        = Column(String, ForeignKey("customers.id"), nullable=False)
    receiver_id      = Column(String, ForeignKey("customers.id"), nullable=True)
    merchant_id      = Column(String, ForeignKey("merchants.id"), nullable=True)
    device_id        = Column(String, ForeignKey("devices.id"), nullable=True)

    amount           = Column(Float, nullable=False)
    currency         = Column(String(5), default="INR")
    location         = Column(String(100))
    latitude         = Column(Float)
    longitude        = Column(Float)

    transaction_type = Column(Enum(TransactionType), default=TransactionType.transfer)
    status           = Column(Enum(TransactionStatus), default=TransactionStatus.completed)

    risk_score       = Column(Float, default=0.0)
    risk_category    = Column(Enum(RiskCategory), default=RiskCategory.low)
    fraud_label      = Column(Boolean, default=False)
    fraud_reasons    = Column(Text)  # JSON string of triggered fraud rules

    timestamp        = Column(DateTime(timezone=True), server_default=func.now())
    processed_at     = Column(DateTime(timezone=True))

    # Relationships
    sender   = relationship("Customer", foreign_keys=[sender_id],   back_populates="sent_transactions")
    receiver = relationship("Customer", foreign_keys=[receiver_id], back_populates="received_transactions")
    merchant = relationship("Merchant", back_populates="transactions")
    device   = relationship("Device",   back_populates="transactions")
    alerts   = relationship("FraudAlert", back_populates="transaction")
    risk_record = relationship("RiskScore", back_populates="transaction", uselist=False)


class FraudAlert(Base):
    """Fraud alert raised when a transaction is flagged."""
    __tablename__ = "fraud_alerts"

    id             = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), nullable=False)
    alert_type     = Column(String(50))  # velocity, device_sharing, ring, location_anomaly, etc.
    severity       = Column(Enum(AlertSeverity), default=AlertSeverity.medium)
    status         = Column(Enum(AlertStatus),   default=AlertStatus.open)
    description    = Column(Text)
    triggered_rules = Column(Text)  # JSON list of triggered rules
    risk_score     = Column(Float)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at    = Column(DateTime(timezone=True))
    resolved_by    = Column(String, ForeignKey("users.id"), nullable=True)

    transaction = relationship("Transaction", back_populates="alerts")
    notes       = relationship("InvestigationNote", back_populates="alert")


class RiskScore(Base):
    """Detailed risk scoring record for each analyzed transaction."""
    __tablename__ = "risk_scores"

    id             = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), unique=True)
    overall_score  = Column(Float, default=0.0)       # 0–100

    # Component scores
    rule_score     = Column(Float, default=0.0)       # Rule-based score
    ml_score       = Column(Float, default=0.0)       # ML anomaly score
    graph_score    = Column(Float, default=0.0)       # Graph pattern score

    # Individual flags
    high_amount_flag     = Column(Boolean, default=False)
    velocity_flag        = Column(Boolean, default=False)
    device_sharing_flag  = Column(Boolean, default=False)
    location_anomaly_flag = Column(Boolean, default=False)
    ring_pattern_flag    = Column(Boolean, default=False)
    unusual_hours_flag   = Column(Boolean, default=False)
    new_merchant_flag    = Column(Boolean, default=False)

    explanation    = Column(Text)   # Human-readable explanation
    analyzed_at    = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("Transaction", back_populates="risk_record")


class InvestigationNote(Base):
    """Notes added by investigators during fraud case review."""
    __tablename__ = "investigation_notes"

    id             = Column(String, primary_key=True, default=generate_uuid)
    alert_id       = Column(String, ForeignKey("fraud_alerts.id"), nullable=False)
    investigator_id = Column(String, ForeignKey("users.id"), nullable=False)
    note_text      = Column(Text, nullable=False)
    action_taken   = Column(String(100))  # blocked_account | contacted_customer | escalated | etc.
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    alert        = relationship("FraudAlert",        back_populates="notes")
    investigator = relationship("User", back_populates="notes")
