from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (ReviewRequest, TransactionCreate, TransactionDetail, TransactionOut)
from app.services import transaction_service as svc

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _filters(risk_level: Optional[str] = Query(None, pattern="^(?i)(LOW|MEDIUM|HIGH|CRITICAL)$"),
             status: Optional[str] = Query(None, pattern="^(?i)(NORMAL|FLAGGED|REVIEWED|CLEARED)$"),
             rule: Optional[str] = None, date: Optional[date] = None,
             search: Optional[str] = Query(None, max_length=64),
             limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return dict(risk_level=risk_level, status=status, rule=rule, on_date=date, search=search, limit=limit, offset=offset)


def _detail(db: Session, txn) -> TransactionDetail:
    return TransactionDetail.model_validate({
        **TransactionOut.model_validate(txn).model_dump(),
        "reviews": txn.reviews, "explanation": svc.explain(txn),
        "customer_history": [TransactionOut.model_validate(t) for t in svc.customer_history(db, txn)],
    })


@router.post("", response_model=TransactionDetail, status_code=201)
def create(payload: TransactionCreate, db: Session = Depends(get_db)):
    try:
        txn = svc.create_transaction(db, payload)
    except svc.DuplicateTransaction as exc:
        raise HTTPException(409, f"Transaction {exc} already exists")
    return _detail(db, svc.get_transaction(db, txn.transaction_id))


@router.get("", response_model=list[TransactionOut])
def list_all(f: dict = Depends(_filters), db: Session = Depends(get_db)):
    return svc.list_transactions(db, **f)


@router.get("/flagged", response_model=list[TransactionOut])
def list_flagged(f: dict = Depends(_filters), db: Session = Depends(get_db)):
    return svc.list_transactions(db, flagged_only=True, **f)


@router.get("/{transaction_id}", response_model=TransactionDetail)
def detail(transaction_id: str, db: Session = Depends(get_db)):
    try:
        return _detail(db, svc.get_transaction(db, transaction_id))
    except svc.TransactionNotFound:
        raise HTTPException(404, "Transaction not found")


def _act(action: str, transaction_id: str, body: ReviewRequest, db: Session):
    try:
        txn = svc.apply_review(db, transaction_id, action, body.reviewer.strip(), body.comments)
    except svc.TransactionNotFound:
        raise HTTPException(404, "Transaction not found")
    return _detail(db, txn)


@router.post("/{transaction_id}/review", response_model=TransactionDetail)
def review(transaction_id: str, body: ReviewRequest, db: Session = Depends(get_db)):
    return _act("REVIEWED", transaction_id, body, db)


@router.post("/{transaction_id}/clear", response_model=TransactionDetail)
def clear(transaction_id: str, body: ReviewRequest, db: Session = Depends(get_db)):
    return _act("CLEARED", transaction_id, body, db)
