from sqlalchemy import Column, Integer, String, Numeric, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)  # business id, e.g. TXN-AB12CD34EF
    customer_id = Column(String(32), index=True, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    city = Column(String(64))
    merchant = Column(String(120))
    status = Column(String(16), nullable=False, default="NORMAL", index=True)  # NORMAL | FLAGGED | REVIEWED | CLEARED
    risk_score = Column(Integer, nullable=False, default=0)
    risk_level = Column(String(16), nullable=False, default="LOW", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    flags = relationship("FraudFlag", back_populates="transaction", cascade="all, delete-orphan", order_by="FraudFlag.id")
    reviews = relationship("Review", back_populates="transaction", cascade="all, delete-orphan", order_by="Review.id")


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), index=True, nullable=False)
    rule_name = Column(String(64), index=True, nullable=False)
    reason = Column(Text, nullable=False)
    risk_points = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("Transaction", back_populates="flags")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), index=True, nullable=False)
    reviewer = Column(String(80), nullable=False)
    action = Column(String(16), nullable=False)  # REVIEWED | CLEARED
    comments = Column(Text)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("Transaction", back_populates="reviews")


class NotificationLog(Base):
    """Audit trail of high-risk alerts (real or simulated)."""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), index=True, nullable=False)
    channel = Column(String(16), nullable=False)   # DEMO | SNS | SES
    status = Column(String(16), nullable=False)    # SIMULATED | SENT | FAILED
    subject = Column(String(200))
    message = Column(Text)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("Transaction")
