from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EscalationCreate, EscalationOut, EscalationStatusUpdate, TransactionDetail, TransactionOut
from app.services import transaction_service as svc

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


def _detail(db: Session, txn) -> TransactionDetail:
    return TransactionDetail.model_validate({
        **TransactionOut.model_validate(txn).model_dump(),
        "reviews": txn.reviews,
        "escalations": [EscalationOut.model_validate(e) for e in txn.escalations],
        "explanation": svc.explain(txn),
        "customer_history": [TransactionOut.model_validate(t) for t in svc.customer_history(db, txn)],
    })


@router.post("/{transaction_id}", response_model=TransactionDetail, status_code=200)
def escalate_case(transaction_id: str, body: EscalationCreate, db: Session = Depends(get_db)):
    try:
        txn = svc.escalate_transaction(
            db,
            transaction_id=transaction_id,
            reviewer=body.reviewer.strip() if body.reviewer else "analyst",
            reason=body.reason.strip() if body.reason else None,
            destination=body.destination.strip() if body.destination else "CYBER_CRIME"
        )
        return _detail(db, txn)
    except svc.TransactionNotFound:
        raise HTTPException(404, f"Transaction {transaction_id} not found")
    except svc.IneligibleForEscalation as exc:
        raise HTTPException(400, str(exc))


@router.get("", response_model=list[EscalationOut])
def list_escalations(
    status: Optional[str] = Query(None, pattern="^(?i)(NOT ESCALATED|ESCALATION PENDING|ESCALATED|UNDER INVESTIGATION|RESOLVED)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    rows = svc.list_escalations(db, status=status, limit=limit, offset=offset)
    return [EscalationOut.model_validate(r) for r in rows]


@router.get("/{transaction_id}", response_model=list[EscalationOut])
def get_escalations_for_transaction(transaction_id: str, db: Session = Depends(get_db)):
    try:
        txn = svc.get_transaction(db, transaction_id)
        return [EscalationOut.model_validate(e) for e in txn.escalations]
    except svc.TransactionNotFound:
        raise HTTPException(404, f"Transaction {transaction_id} not found")


@router.patch("/{transaction_id}/status", response_model=TransactionDetail)
def update_status(transaction_id: str, body: EscalationStatusUpdate, db: Session = Depends(get_db)):
    try:
        txn = svc.update_escalation_status(db, transaction_id, body.status, body.notes)
        return _detail(db, txn)
    except svc.TransactionNotFound:
        raise HTTPException(404, f"Transaction {transaction_id} or escalation record not found")
