# Fraud Rule Engine with Reviewer Console

A working hackathon prototype: transactions are scored by a **pluggable rule engine**, stored in PostgreSQL with their fraud flags, and investigated in a **React reviewer console**. Critical scores (≥ 80) raise an **AWS SNS/SES alert**, or a simulated one in demo mode.

> **All data is DEMO DATA.** Customers, amounts and merchants are fictional. Never load real banking data.

## 1. Features
- Three independent rules: transaction velocity, unusual amount, impossible geography (Haversine)
- Rules are auto-discovered: **add a file, restart, done**. The engine never changes
- Configurable points, thresholds, risk levels and flag threshold via `.env`
- Explainable flags: every hit stores a human-readable reason with the numbers behind it
- Reviewer workflow: Mark as reviewed / Clear, with reviewer name and comment, persisted
- Dashboard: 6 summary cards, 3 charts, filters (risk, status, rule, date, search), detail modal
- One-click **Generate demo transactions** covering all scenarios
- Alert audit trail (`notification_logs`) shown in the console

## 2. Architecture
```
Transaction ─▶ POST /transactions ─▶ transaction_service
                                          │ loads customer history
                                          ▼
                                     RuleEngine ──▶ [VelocityRule, UnusualAmountRule, ImpossibleGeographyRule, …]
                                          │ sum points (cap 100) ─▶ risk level ─▶ flagged?
                                          ▼
                     PostgreSQL: transactions + fraud_flags
                                          │ score ≥ ALERT_THRESHOLD
                                          ▼
                              NotificationService ─▶ DEMO log  |  AWS SNS  |  AWS SES
React console ◀── REST ──▶ list / detail / review / clear / stats
```

## 3. Tech stack
React 18 + Vite + Recharts · FastAPI + Pydantic v2 · SQLAlchemy 2 + PostgreSQL 16 · boto3 (SNS/SES)

## 4. Project structure
```
fraud-rule-engine/
├── docker-compose.yml            PostgreSQL only
├── backend/
│   ├── app/
│   │   ├── main.py               FastAPI app, CORS, startup
│   │   ├── config.py             env-driven settings
│   │   ├── database.py           engine, session, init_db()
│   │   ├── models/               Transaction, FraudFlag, Review, NotificationLog
│   │   ├── schemas/              Pydantic request/response models
│   │   ├── api/                  transactions.py, dashboard.py (stats, rules, alerts, demo)
│   │   ├── services/             transaction_service.py, demo_service.py
│   │   ├── rules/                base_rule.py, velocity_rule.py, amount_rule.py, geography_rule.py
│   │   ├── engine/               rule_engine.py (generic), __init__.py (auto-loads rules)
│   │   └── notifications/        notification_service.py
│   ├── examples/device_rule.py   sample extra rule (inactive)
│   ├── seed_data.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/{components,pages,services}, App.jsx, main.jsx, index.css
    ├── package.json
    └── .env.example
```
Two additions to your suggested layout: `config.py`/`utils.py` (settings and helpers shared by rules) and a `notification_logs` table (so the alert shows up in the UI in demo mode).

## 5. Database setup
**Docker (easiest):** `docker compose up -d db`

**Existing PostgreSQL:**
```sql
CREATE USER fraud_user WITH PASSWORD 'fraud_pass';
CREATE DATABASE fraud_db OWNER fraud_user;
```
Tables are created automatically on backend startup (`init_db()`), or run `python seed_data.py`.

| Table | Key columns |
|---|---|
| `transactions` | id, transaction_id (unique business id), customer_id, amount, timestamp, latitude, longitude, city, merchant, status, risk_score, risk_level, created_at |
| `fraud_flags` | id, transaction_id → transactions.id, rule_name, reason, risk_points, created_at |
| `reviews` | id, transaction_id → transactions.id, reviewer, action, comments, reviewed_at |
| `notification_logs` | id, transaction_id → transactions.id, channel, status, subject, message, error, created_at |

`status`: NORMAL → FLAGGED (score ≥ FRAUD_THRESHOLD) → REVIEWED / CLEARED.

## 6. Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```
Swagger UI: http://localhost:8000/docs

## 7. Frontend setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev                        # http://localhost:5173
```

## 8. Environment variables
| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL | `postgresql+psycopg2://fraud_user:fraud_pass@localhost:5432/fraud_db` |
| `DEMO_MODE` | `true` = simulate alerts, no AWS | `true` |
| `NOTIFY_CHANNEL` | `sns` or `ses` (when DEMO_MODE=false) | `sns` |
| `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS access (boto3 reads these from the environment) | – |
| `SNS_TOPIC_ARN` | SNS topic | – |
| `SES_SENDER_EMAIL`, `SES_RECIPIENT_EMAIL` | verified SES addresses | – |
| `RISK_MEDIUM_MIN` / `RISK_HIGH_MIN` / `RISK_CRITICAL_MIN` | level boundaries | 30 / 60 / 80 |
| `FRAUD_THRESHOLD` | score at which a transaction is FLAGGED | 30 |
| `ALERT_THRESHOLD` | score that triggers an alert | 80 |
| `VELOCITY_MAX_TXNS`, `VELOCITY_WINDOW_MINUTES`, `VELOCITY_POINTS` | Rule 1 | 6 / 5 / 30 |
| `AMOUNT_MULTIPLIER`, `AMOUNT_MIN_HISTORY`, `AMOUNT_FALLBACK_THRESHOLD`, `AMOUNT_POINTS` | Rule 2 | 5 / 3 / 50000 / 40 |
| `GEO_MAX_SPEED_KMH`, `GEO_MIN_DISTANCE_KM`, `GEO_POINTS` | Rule 3 | 900 / 50 / 30 |
| `DISABLED_RULES` | comma-separated rule names to switch off | – |
| `VITE_API_URL` (frontend) | API base URL | `http://localhost:8000` |

## 9. Running & demo data
Start the backend and frontend, then either click **Generate demo transactions** in the console, or run `python seed_data.py` (creates customers C1001–C1005 and prints each scenario's score). Each click of the button uses new customer IDs, so scenarios never interfere with each other.

| Scenario | What it does | Result |
|---|---|---|
| Normal | ₹850 in Chennai, typical history | LOW (0) |
| Unusual amount | history ₹500/800/1,200/700, then ₹90,000 | MEDIUM (40) |
| Velocity | 7 small transactions in 4 min | MEDIUM (30) on the 6th and 7th |
| Impossible location | Chennai, then Mumbai 20 min later with ₹25,000 | HIGH (70 = geography 30 + amount 40) |
| Multiple rules | burst in Chennai, then ₹1,20,000 in Delhi seconds later | CRITICAL (100), alert sent |

Note: scores follow the point values you specified (30/40/30). A single rule alone therefore lands in MEDIUM; HIGH needs two rules together. Change the `*_POINTS` values or level boundaries in `.env` if you want a single rule to reach HIGH.

## 10. API documentation
| Method | Path | Description |
|---|---|---|
| POST | `/transactions` | Create + evaluate. Omit `transaction_id` and `timestamp` to auto-generate |
| GET | `/transactions` | List. Filters: `risk_level`, `status`, `rule`, `date` (YYYY-MM-DD, UTC), `search`, `limit`, `offset` |
| GET | `/transactions/flagged` | Same filters, only score ≥ FRAUD_THRESHOLD |
| GET | `/transactions/{transaction_id}` | Detail, triggered rules, explanation, review log, customer history |
| POST | `/transactions/{transaction_id}/review` | Body `{"reviewer": "...", "comments": "..."}`. Sets REVIEWED |
| POST | `/transactions/{transaction_id}/clear` | Same body. Sets CLEARED |
| GET | `/dashboard/stats` | Cards, chart data, demo mode flag |
| GET | `/rules` | Registered rules with live config |
| GET | `/notifications` | Recent alerts (real or simulated) |
| POST | `/demo/generate` | Generate the demo scenario batch |
| GET | `/health` | DB check + loaded rules |

Example: an impossible-travel test with curl (run the two calls back to back):
```bash
curl -X POST localhost:8000/transactions -H 'Content-Type: application/json' \
  -d '{"customer_id":"T1","amount":900,"latitude":13.0827,"longitude":80.2707,"city":"Chennai"}'
curl -X POST localhost:8000/transactions -H 'Content-Type: application/json' \
  -d '{"customer_id":"T1","amount":900,"latitude":19.0760,"longitude":72.8777,"city":"Mumbai"}'
```
The second is flagged: 1,030 km in seconds. Distance uses the Haversine formula on stored lat/lon, never city names.

## 11. How the rule engine works
1. `POST /transactions` builds a `Transaction`, loads that customer's last 50 earlier transactions into a `RuleContext`.
2. `RuleEngine.evaluate()` runs every registered rule. Each returns a `RuleResult(triggered, risk_points, reason)`.
3. Score = sum of triggered points, capped at 100. Level comes from the configurable boundaries. FLAGGED if score ≥ `FRAUD_THRESHOLD`.
4. The transaction and one `fraud_flags` row per triggered rule are saved. Score ≥ `ALERT_THRESHOLD` calls the notification service.
5. A rule that raises an exception is logged and skipped, so one bad rule never breaks scoring.

**Rule 1: Velocity.** Counts the customer's transactions in the last `VELOCITY_WINDOW_MINUTES`, including the current one. Triggers at `VELOCITY_MAX_TXNS` or more (default 6 in 5 min, +30).

**Rule 2: Unusual amount.** *Method implemented:* customer historical average × configurable multiplier. With at least `AMOUNT_MIN_HISTORY` (3) prior clean transactions, it triggers when `amount > average × AMOUNT_MULTIPLIER` (default 5×, +40). Prior transactions that scored ≥ 30 are excluded from the baseline so fraud cannot raise "normal". With too little history it falls back to a fixed threshold (`AMOUNT_FALLBACK_THRESHOLD`, ₹50,000).

**Rule 3: Impossible geography.** Haversine distance to the previous transaction divided by elapsed time. Triggers when distance ≥ `GEO_MIN_DISTANCE_KM` and speed > `GEO_MAX_SPEED_KMH` (900, +30).

## 12. How to add a new rule
1. Create `backend/app/rules/device_rule.py` (a ready example is in `backend/examples/device_rule.py`):
```python
from app.rules.base_rule import BaseRule, RuleContext, RuleResult

class RoundAmountRule(BaseRule):
    name = "round_amount"
    display_name = "Suspicious Round Amount"
    description = "Flags large round-number amounts."
    def __init__(self):
        self.points = 15
    def evaluate(self, txn, ctx: RuleContext) -> RuleResult:
        if float(txn.amount) >= 10000 and float(txn.amount) % 1000 == 0:
            return self.hit("Large round-number amount")
        return self.ok()
```
2. Restart the backend. `app/rules/__init__.py` auto-discovers any `BaseRule` subclass in the package.

The rule then appears in `GET /rules`, the console's rule filter, the Active Rules panel and the charts. No change to `RuleEngine`, the API or the frontend. Verified by dropping in the example file. Switch a rule off with `DISABLED_RULES=round_amount`.

## 13. AWS SNS / SES setup
Set `DEMO_MODE=false`, then either:

**SNS:** create a topic and subscribe your email (confirm the subscription email). Set `NOTIFY_CHANNEL=sns`, `SNS_TOPIC_ARN`, `AWS_REGION`. The IAM identity needs `sns:Publish` on that topic.

**SES:** verify sender and recipient addresses (SES sandbox requires both). Set `NOTIFY_CHANNEL=ses`, `SES_SENDER_EMAIL`, `SES_RECIPIENT_EMAIL`. The IAM identity needs `ses:SendEmail`.

Credentials come from `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` in your environment or `.env`, or an IAM role. They are never in source. Delivery failures are stored as `FAILED` with the error and shown in the console, and never block the transaction.

## 14. Troubleshooting
| Problem | Fix |
|---|---|
| `connection refused` on startup | PostgreSQL is not running: `docker compose up -d db`, check `DATABASE_URL` |
| Console shows "Cannot reach the API" | Backend not running, or `VITE_API_URL` wrong. Restart `npm run dev` after editing `.env` |
| CORS error in browser | Add your frontend origin to `CORS_ORIGINS` |
| `psycopg2` install fails | Use `psycopg2-binary` (already in requirements) and Python 3.10+ |
| No alert in live mode | Check the alert's `FAILED` error in the console; verify SNS subscription / SES identities and region |
| Empty console | Click **Generate demo transactions** |
| Want a clean slate | `docker compose down -v` then `up -d db` |

## 15. Hackathon demo flow (3 minutes)
**0:00–0:30, Problem and architecture.** "Banks need explainable fraud detection that changes as fraud changes." Show the pipeline diagram: pluggable rules, score, level, store, review, alert.

**0:30–1:15, Generate and explore.** Click **Generate demo transactions**. Cards, charts and the flagged table update. Point at the risk meters and rule chips. Open Active Rules to show the configurable thresholds.

**1:15–2:00, Explainability.** Open the CRITICAL transaction (₹1,20,000, Delhi). Read the *Rule explanation*: "3 rules triggered: 7 transactions within 5 minutes; 208× the customer's average; 1,753 km away only seconds earlier." Show customer history. "No black box: every point is justified."

**2:00–2:30, Reviewer workflow.** Type a comment, click **Mark as reviewed**, then open another flagged item and **Clear transaction**. Watch Pending Review and Cleared cards change. State that it is persisted in PostgreSQL (`reviews` table).

**2:30–3:00, Alert and extensibility.** Show the High-risk alerts panel (simulated in demo, SNS/SES with `DEMO_MODE=false`). Close: "Adding a new rule is one file. Drop `device_rule.py` into `app/rules/` and it appears everywhere." Optionally do it live.

## 16. Cyber Crime / Fraud Escalation Workflow

The application includes an end-to-end escalation system for high-risk and critical fraud cases:

```
Detect ─▶ Score ─▶ Explain ─▶ Prioritize ─▶ Human Reviewer ─▶ Escalate to Cyber Crime
```

### Escalation Features & Human-in-the-Loop Safeguard
1. **Eligibility**: Transactions scoring **HIGH** (60–79) or **CRITICAL** (80–100) are automatically identified and made eligible for escalation.
2. **Reviewer Decision**: Escalation is **never fully automated**. A human reviewer inspects the explainable rule breakdown, customer transaction history, and risk score before explicitly clicking **"Escalate to Cyber Crime"**.
3. **Escalation Data Record**:
   - `transaction_id`, `customer_id`, `amount`, `location`, `timestamp`
   - `risk_score` & `risk_level`
   - `triggered_rules` breakdown & explanation
   - `escalated_by` (reviewer name) & `escalated_at` timestamp
   - `status`: `NOT ESCALATED` | `ESCALATION PENDING` | `ESCALATED` | `UNDER INVESTIGATION` | `RESOLVED`
4. **Dashboard Alerts & Filtering**:
   - Prominent 🚨 **Escalated Fraud Alerts** panel on the reviewer dashboard.
   - **Escalated Cases** KPI card in the summary header.
   - Dedicated **Escalated cases** filter tab for quick triage.
   - **Escalation History** log embedded in the transaction detail modal.

### Hackathon Prototype vs. Production Integration
> [!NOTE]
> For the hackathon prototype, the application **does NOT connect to any official government Cyber Crime reporting API or external portal**.
> 
> When the reviewer clicks **"Escalate to Cyber Crime"**, the system executes a **simulated prototype escalation protocol**:
> - Logs a simulated dispatch (`CYBER_CRIME` channel) in `notification_logs`.
> - Updates the database record to `ESCALATED`.
> - Displays: *"Case successfully escalated to Cyber Crime Investigation Queue."*
> 
> **Production Integration Path**: The clean notification service abstraction (`NotificationService`) is structured so that bank fraud infrastructure teams can plug in:
> - Production Email / SMS alerts to internal fraud investigation teams.
> - Webhooks or APIs connecting to official bank/government cyber-crime reporting channels.
> - AWS SNS/SQS messaging queues for automated law-enforcement ticketing systems.

## 17. Test checklist
1. **Velocity:** Generate demo, filter Rule = Transaction Velocity. Expect the 6th/7th burst transactions, reason "7 transactions within 5 minutes".
2. **Amount:** Filter Rule = Unusual Amount. Expect ₹90,000 with a ratio against the ₹800 average.
3. **Geography:** Filter Rule = Impossible Geographical Location. Expect the Chennai→Mumbai case with distance and speed.
4. **Reviewer actions:** open a flagged row, add a comment, click Mark as reviewed or Clear. Refresh the page; status persists. Confirm with `SELECT * FROM reviews;`.
5. **Notification:** open the CRITICAL row. The alerts panel lists it; backend logs show `DEMO NOTIFICATION`. With `DEMO_MODE=false`, check your inbox.
6. **Escalation:** Open transaction `C1005` (score 100/100 CRITICAL). Verify 🚨 CRITICAL FRAUD ALERT box and checkmarks. Click **"Escalate to Cyber Crime"**. Confirm toast *"Case successfully escalated to Cyber Crime Investigation Queue."*, status changes to `ESCALATED`, KPI updates, and escalation history is recorded.
