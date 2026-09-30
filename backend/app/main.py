import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import dashboard, transactions
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.engine import get_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
settings = get_settings()

app = FastAPI(title="Fraud Rule Engine API", version="1.0.0",
              description="Rule-based fraud scoring with a reviewer workflow. Demo data only.")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    init_db()
    names = [r.name for r in get_engine().rules]
    logging.getLogger("fraud").info("Loaded rules: %s | DEMO_MODE=%s", names, settings.demo_mode)


@app.get("/health", tags=["health"])
def health():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "demo_mode": settings.demo_mode, "rules": [r.name for r in get_engine().rules]}


app.include_router(transactions.router)
app.include_router(dashboard.router)
