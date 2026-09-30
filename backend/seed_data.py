"""Seed the database with DEMO DATA (fictional customers C1001-C1005).
Usage:  python seed_data.py
"""
from app.database import SessionLocal, init_db
from app.services.demo_service import generate_demo_batch

if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        result = generate_demo_batch(db, customer_base=1001)
    print(result["note"])
    for s in result["scenarios"]:
        print(f"  {s['customer_id']}  {s['scenario']:<40} score={s['risk_score']:>3}  {s['risk_level']:<8} (expected {s['expected']})")
