"""Demo data generator. Every value here is FAKE / for demonstration only."""
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Transaction
from app.schemas import TransactionCreate
from app.services.transaction_service import create_transaction

CITIES = {
    "Chennai": (13.0827, 80.2707), "Mumbai": (19.0760, 72.8777), "Bengaluru": (12.9716, 77.5946),
    "Delhi": (28.6139, 77.2090), "Hyderabad": (17.3850, 78.4867),
}
MERCHANTS = ["Demo Grocers", "Demo Fuel Station", "Demo Electronics", "Demo Pharmacy", "Demo Cafe", "Demo Online Mart"]


def _make(db, cust, amount, ts, city, merchant=None):
    lat, lon = CITIES[city]
    return create_transaction(db, TransactionCreate(
        customer_id=cust, amount=amount, timestamp=ts,
        latitude=lat + random.uniform(-0.02, 0.02), longitude=lon + random.uniform(-0.02, 0.02),
        city=city, merchant=merchant or random.choice(MERCHANTS)))


def _baseline(db, cust, city, amounts, now):
    """Normal spending history, one transaction every ~3 hours before `now`."""
    n = len(amounts)
    for i, amt in enumerate(amounts):
        _make(db, cust, amt, now - timedelta(hours=(n - i) * 3 + 1, minutes=random.randint(0, 40)), city)


def _pick_base(db):
    while True:
        base = random.randint(3000, 8900)
        if not db.scalar(select(Transaction.id).where(Transaction.customer_id == f"C{base}").limit(1)):
            return base


def generate_demo_batch(db, customer_base: int | None = None) -> dict:
    now = datetime.now(timezone.utc)
    base = customer_base or _pick_base(db)
    c = [f"C{base + i}" for i in range(5)]
    scenarios = []

    def record(name, expected, cust, txn):
        scenarios.append({"scenario": name, "expected": expected, "customer_id": cust,
                          "transaction_id": txn.transaction_id, "risk_score": txn.risk_score, "risk_level": txn.risk_level})

    # 1. NORMAL — ordinary spend
    _baseline(db, c[0], "Chennai", [500, 1200, 700, 950, 600], now)
    record("Normal purchase", "LOW", c[0], _make(db, c[0], 850, now, "Chennai"))

    # 2. UNUSUAL AMOUNT — the spec's example history (500, 800, 1200, 700) then ₹90,000
    _baseline(db, c[1], "Chennai", [500, 800, 1200, 700], now)
    record("Unusual amount (₹90,000)", "MEDIUM (40 pts)", c[1], _make(db, c[1], 90000, now, "Chennai"))

    # 3. VELOCITY — 7 small transactions inside ~4 minutes
    _baseline(db, c[2], "Bengaluru", [600, 900, 700, 1100, 800], now)
    last = None
    for i in range(7):
        last = _make(db, c[2], random.choice([350, 420, 480, 550, 600]), now - timedelta(seconds=240 - i * 40), "Bengaluru")
    record("Rapid transactions (7 in 4 min)", "MEDIUM (30 pts)", c[2], last)

    # 4. IMPOSSIBLE LOCATION — Chennai, then Mumbai 20 minutes later with a large amount
    _baseline(db, c[3], "Chennai", [700, 900, 650, 1000, 800], now)
    _make(db, c[3], 1200, now - timedelta(minutes=20), "Chennai")
    record("Chennai → Mumbai in 20 min, ₹25,000", "HIGH (geo + amount)", c[3], _make(db, c[3], 25000, now, "Mumbai"))

    # 5. MULTIPLE RULES — burst of small spends in Chennai, then ₹1,20,000 in Delhi
    _baseline(db, c[4], "Chennai", [600, 800, 750, 900, 700], now)
    for offset in (270, 210, 150, 90, 45, 30):
        _make(db, c[4], 400, now - timedelta(seconds=offset), "Chennai")
    record("Burst + ₹1,20,000 in Delhi", "CRITICAL (100 pts, alert sent)", c[4], _make(db, c[4], 120000, now, "Delhi"))

    return {"created_customers": c, "scenarios": scenarios,
            "note": "DEMO DATA — fictional customers and transactions."}
