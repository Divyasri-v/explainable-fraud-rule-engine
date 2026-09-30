import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.engine import get_engine
from app.models import FraudFlag, NotificationLog, Review, Transaction
from app.notifications.notification_service import NotificationService
from app.rules.base_rule import RuleContext
from app.schemas import Explanation, TransactionCreate
from app.utils import as_utc

settings = get_settings()
LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class DuplicateTransaction(Exception):
    pass


class TransactionNotFound(Exception):
    pass


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    """Evaluate a transaction against every registered rule, persist it with its flags,
    and raise an alert if the score crosses the alert threshold."""
    tid = payload.transaction_id or f"TXN-{uuid.uuid4().hex[:10].upper()}"
    if db.scalar(select(Transaction.id).where(Transaction.transaction_id == tid)):
        raise DuplicateTransaction(tid)

    ts = as_utc(payload.timestamp) if payload.timestamp else datetime.now(timezone.utc)
    txn = Transaction(transaction_id=tid, customer_id=payload.customer_id, amount=payload.amount,
                      timestamp=ts, latitude=payload.latitude, longitude=payload.longitude,
                      city=payload.city, merchant=payload.merchant)

    history = db.scalars(
        select(Transaction).where(Transaction.customer_id == txn.customer_id, Transaction.timestamp < ts)
        .order_by(Transaction.timestamp.desc()).limit(50)).all()

    result = get_engine().evaluate(txn, RuleContext(history=list(history)))
    txn.risk_score, txn.risk_level = result.score, result.level
    txn.status = "FLAGGED" if result.flagged else "NORMAL"
    for rule, res in result.triggered:
        txn.flags.append(FraudFlag(rule_name=rule.name, reason=res.reason, risk_points=res.risk_points))

    db.add(txn)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateTransaction(tid)
    db.refresh(txn)

    if txn.risk_score >= settings.alert_threshold:
        NotificationService().send_high_risk_alert(db, txn)
    return txn


def get_transaction(db: Session, transaction_id: str) -> Transaction:
    txn = db.scalar(select(Transaction).options(selectinload(Transaction.flags), selectinload(Transaction.reviews))
                    .where(Transaction.transaction_id == transaction_id))
    if not txn:
        raise TransactionNotFound(transaction_id)
    return txn


def list_transactions(db: Session, *, flagged_only=False, risk_level: Optional[str] = None,
                      status: Optional[str] = None, rule: Optional[str] = None,
                      on_date: Optional[date] = None, search: Optional[str] = None,
                      limit: int = 100, offset: int = 0):
    q = select(Transaction).options(selectinload(Transaction.flags))
    if flagged_only:
        q = q.where(Transaction.risk_score >= settings.fraud_threshold)
    if risk_level:
        q = q.where(Transaction.risk_level == risk_level.upper())
    if status:
        q = q.where(Transaction.status == status.upper())
    if rule:
        q = q.where(Transaction.flags.any(FraudFlag.rule_name == rule))
    if on_date:
        start = datetime.combine(on_date, datetime.min.time(), tzinfo=timezone.utc)
        q = q.where(Transaction.timestamp >= start, Transaction.timestamp < start + timedelta(days=1))
    if search:
        like = f"%{search.strip()}%"
        q = q.where(Transaction.transaction_id.ilike(like) | Transaction.customer_id.ilike(like))
    q = q.order_by(Transaction.timestamp.desc(), Transaction.id.desc()).limit(limit).offset(offset)
    return db.scalars(q).all()


def customer_history(db: Session, txn: Transaction, limit: int = 8):
    return db.scalars(
        select(Transaction).options(selectinload(Transaction.flags))
        .where(Transaction.customer_id == txn.customer_id, Transaction.id != txn.id)
        .order_by(Transaction.timestamp.desc()).limit(limit)).all()


def explain(txn: Transaction) -> Explanation:
    n = len(txn.flags)
    if n == 0:
        return Explanation(headline="No rules triggered — this transaction looks normal.", lines=[])
    return Explanation(headline=f"{n} rule{'s' if n != 1 else ''} triggered:", lines=[f.reason for f in txn.flags])


def apply_review(db: Session, transaction_id: str, action: str, reviewer: str, comments: Optional[str]) -> Transaction:
    txn = get_transaction(db, transaction_id)
    txn.status = action  # REVIEWED | CLEARED
    db.add(Review(transaction_id=txn.id, reviewer=reviewer, action=action, comments=comments))
    db.commit()
    return get_transaction(db, transaction_id)


def dashboard_stats(db: Session) -> dict:
    total = db.scalar(select(func.count(Transaction.id))) or 0
    flagged = db.scalar(select(func.count(Transaction.id)).where(Transaction.risk_score >= settings.fraud_threshold)) or 0
    by_level = {lvl: 0 for lvl in LEVELS}
    for lvl, n in db.execute(select(Transaction.risk_level, func.count()).group_by(Transaction.risk_level)):
        by_level[lvl] = n
    by_status = {s: n for s, n in db.execute(select(Transaction.status, func.count()).group_by(Transaction.status))}
    flags_by_rule = {r: n for r, n in db.execute(select(FraudFlag.rule_name, func.count()).group_by(FraudFlag.rule_name))}

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    buckets = {now - timedelta(hours=i): {"total": 0, "flagged": 0} for i in range(23, -1, -1)}
    since = now - timedelta(hours=23)
    for ts, score in db.execute(select(Transaction.timestamp, Transaction.risk_score).where(Transaction.timestamp >= since)):
        key = as_utc(ts).replace(minute=0, second=0, microsecond=0)
        if key in buckets:
            buckets[key]["total"] += 1
            buckets[key]["flagged"] += 1 if score >= settings.fraud_threshold else 0
    activity = [{"hour": k.isoformat(), **v} for k, v in buckets.items()]

    return {
        "total_transactions": total, "flagged_transactions": flagged,
        "high_risk": by_level["HIGH"], "critical_risk": by_level["CRITICAL"],
        "cleared": by_status.get("CLEARED", 0), "reviewed": by_status.get("REVIEWED", 0),
        "pending_review": by_status.get("FLAGGED", 0),
        "by_risk_level": by_level, "flags_by_rule": flags_by_rule, "activity": activity,
        "demo_mode": settings.demo_mode,
    }


def recent_notifications(db: Session, limit: int = 10):
    rows = db.execute(select(NotificationLog, Transaction.transaction_id)
                      .join(Transaction, Transaction.id == NotificationLog.transaction_id)
                      .order_by(NotificationLog.id.desc()).limit(limit)).all()
    return [(n, ref) for n, ref in rows]
