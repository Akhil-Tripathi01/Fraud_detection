"""
Pydantic Schemas
Request/response validation models for all API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import (
    TransactionType, TransactionStatus, RiskCategory,
    AlertStatus, AlertSeverity
)


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username:  str = Field(..., min_length=3, max_length=50)
    email:     EmailStr
    password:  str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role:      Optional[str] = "investigator"


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      str
    username:     str
    role:         str


class UserOut(BaseModel):
    id:         str
    username:   str
    email:      str
    full_name:  Optional[str]
    role:       str
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Customer Schemas ─────────────────────────────────────────────────────────

class CustomerOut(BaseModel):
    id:             str
    name:           str
    email:          str
    phone:          Optional[str]
    account_number: str
    account_type:   str
    balance:        float
    city:           Optional[str]
    country:        str
    is_flagged:     bool
    risk_score:     float
    created_at:     datetime

    class Config:
        from_attributes = True


# ─── Transaction Schemas ──────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    sender_id:        str
    receiver_id:      Optional[str] = None
    merchant_id:      Optional[str] = None
    device_id:        Optional[str] = None
    amount:           float = Field(..., gt=0)
    currency:         str   = "INR"
    location:         Optional[str] = None
    latitude:         Optional[float] = None
    longitude:        Optional[float] = None
    transaction_type: TransactionType = TransactionType.transfer


class TransactionOut(BaseModel):
    transaction_id:   str
    sender_id:        str
    receiver_id:      Optional[str]
    merchant_id:      Optional[str]
    device_id:        Optional[str]
    amount:           float
    currency:         str
    location:         Optional[str]
    transaction_type: str
    status:           str
    risk_score:       float
    risk_category:    str
    fraud_label:      bool
    fraud_reasons:    Optional[str]
    timestamp:        datetime

    class Config:
        from_attributes = True


class TransactionDetail(TransactionOut):
    sender:   Optional[CustomerOut]
    merchant: Optional[Dict[str, Any]]
    device:   Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# ─── Fraud Schemas ────────────────────────────────────────────────────────────

class FraudAnalysisResult(BaseModel):
    transaction_id: str
    risk_score:     float
    risk_category:  str
    fraud_label:    bool
    fraud_reasons:  List[str]
    rule_score:     float
    ml_score:       float
    graph_score:    float
    flags:          Dict[str, bool]
    explanation:    str
    alert_created:  bool
    alert_id:       Optional[str]


class RiskScoreOut(BaseModel):
    transaction_id:        str
    overall_score:         float
    risk_category:         str
    rule_score:            float
    ml_score:              float
    graph_score:           float
    high_amount_flag:      bool
    velocity_flag:         bool
    device_sharing_flag:   bool
    location_anomaly_flag: bool
    ring_pattern_flag:     bool
    unusual_hours_flag:    bool
    new_merchant_flag:     bool
    explanation:           Optional[str]
    analyzed_at:           datetime

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id:              str
    transaction_id:  str
    alert_type:      str
    severity:        str
    status:          str
    description:     Optional[str]
    triggered_rules: Optional[str]
    risk_score:      Optional[float]
    created_at:      datetime
    resolved_at:     Optional[datetime]

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status:   AlertStatus
    note:     Optional[str] = None


# ─── Graph Schemas ────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id:         str
    label:      str
    node_type:  str          # customer | merchant | device | location
    properties: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    source:          str
    target:          str
    edge_type:       str     # transaction | device_use | location_visit
    weight:          float = 1.0
    properties:      Dict[str, Any] = {}


class GraphNetwork(BaseModel):
    nodes:          List[GraphNode]
    edges:          List[GraphEdge]
    total_nodes:    int
    total_edges:    int
    suspicious_nodes: List[str]
    fraud_clusters:  List[List[str]]


# ─── Dashboard Schemas ────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_transactions:   int
    total_alerts:         int
    high_risk_count:      int
    medium_risk_count:    int
    low_risk_count:       int
    open_alerts:          int
    resolved_alerts:      int
    fraud_rate_percent:   float
    total_flagged_amount: float
    total_customers:      int
    total_merchants:      int


class DashboardStats(BaseModel):
    daily_transaction_volume:  List[Dict[str, Any]]
    risk_trend:                List[Dict[str, Any]]
    top_flagged_customers:     List[Dict[str, Any]]
    top_flagged_merchants:     List[Dict[str, Any]]
    alert_type_distribution:   Dict[str, int]


class RiskDistribution(BaseModel):
    low:    int
    medium: int
    high:   int
    total:  int
    low_percent:    float
    medium_percent: float
    high_percent:   float


# ─── Investigation Schemas ────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    alert_id:        str
    note_text:       str = Field(..., min_length=5)
    action_taken:    Optional[str] = None


class NoteOut(BaseModel):
    id:              str
    alert_id:        str
    investigator_id: str
    note_text:       str
    action_taken:    Optional[str]
    created_at:      datetime

    class Config:
        from_attributes = True


class InvestigationDetail(BaseModel):
    alert:        AlertOut
    transaction:  Optional[TransactionOut]
    notes:        List[NoteOut]
    risk_score:   Optional[RiskScoreOut]


# ─── Generic Response ─────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True
