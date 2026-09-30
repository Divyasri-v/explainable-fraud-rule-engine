from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ID_PATTERN = r"^[A-Za-z0-9_\-]+$"


class TransactionCreate(BaseModel):
    transaction_id: Optional[str] = Field(None, max_length=64, pattern=ID_PATTERN)
    customer_id: str = Field(..., min_length=1, max_length=32, pattern=ID_PATTERN)
    amount: Decimal = Field(..., gt=0, max_digits=14, decimal_places=2)
    timestamp: Optional[datetime] = None  # defaults to now (UTC)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: Optional[str] = Field(None, max_length=64)
    merchant: Optional[str] = Field(None, max_length=120)


class FlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rule_name: str
    reason: str
    risk_points: int
    created_at: Optional[datetime] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reviewer: str
    action: str
    comments: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_id: str
    customer_id: str
    amount: float
    timestamp: datetime
    latitude: float
    longitude: float
    city: Optional[str] = None
    merchant: Optional[str] = None
    status: str
    risk_score: int
    risk_level: str
    escalation_status: str = "NOT ESCALATED"
    created_at: Optional[datetime] = None
    flags: list[FlagOut] = []

    @field_validator("amount", mode="before")
    @classmethod
    def _amount_to_float(cls, v):
        return float(v)


class Explanation(BaseModel):
    headline: str
    lines: list[str]


class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_id: int
    txn_ref: Optional[str] = None
    customer_id: str
    risk_score: int
    risk_level: str
    triggered_rules: str
    reason: Optional[str] = None
    destination: str
    status: str
    escalated_by: str
    escalated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class EscalationCreate(BaseModel):
    reviewer: str = Field("analyst", min_length=1, max_length=80)
    reason: Optional[str] = Field(None, max_length=1000)
    destination: Optional[str] = Field("CYBER_CRIME", max_length=64)


class EscalationStatusUpdate(BaseModel):
    status: Literal["NOT ESCALATED", "ESCALATION PENDING", "ESCALATED", "UNDER INVESTIGATION", "RESOLVED"]
    notes: Optional[str] = Field(None, max_length=1000)


class TransactionDetail(TransactionOut):
    reviews: list[ReviewOut] = []
    escalations: list[EscalationOut] = []
    explanation: Explanation
    customer_history: list[TransactionOut] = []


class ReviewRequest(BaseModel):
    reviewer: str = Field("analyst", min_length=1, max_length=80)
    comments: Optional[str] = Field(None, max_length=1000)


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_id: int
    channel: str
    status: str
    subject: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    txn_ref: Optional[str] = None  # business transaction id, filled by the API
