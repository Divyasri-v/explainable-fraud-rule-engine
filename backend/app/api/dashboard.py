from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.engine import get_engine
from app.schemas import NotificationOut
from app.services import demo_service, transaction_service as svc

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats")
def stats(db: Session = Depends(get_db)):
    return svc.dashboard_stats(db)


@router.get("/rules")
def rules():
    """Registered rules — the UI uses this for the rule filter and the Rule Explanation panel."""
    return [{"name": r.name, "display_name": r.display_name, "description": r.description,
             "points": r.points, "config": r.config()} for r in get_engine().rules]


@router.get("/notifications", response_model=list[NotificationOut])
def notifications(db: Session = Depends(get_db)):
    out = []
    for n, ref in svc.recent_notifications(db):
        item = NotificationOut.model_validate(n)
        item.txn_ref = ref
        out.append(item)
    return out


@router.post("/demo/generate", status_code=201)
def generate_demo(db: Session = Depends(get_db)):
    return demo_service.generate_demo_batch(db)
