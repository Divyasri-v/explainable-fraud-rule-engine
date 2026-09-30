from datetime import timedelta

from app.config import env_int
from app.rules.base_rule import BaseRule, RuleContext, RuleResult
from app.utils import as_utc


class VelocityRule(BaseRule):
    """Too many transactions by one customer inside a short window."""
    name = "transaction_velocity"
    display_name = "Transaction Velocity"
    description = "Flags customers who make too many transactions within a short time window."

    def __init__(self):
        self.points = env_int("VELOCITY_POINTS", 30)
        self.max_txns = env_int("VELOCITY_MAX_TXNS", 6)
        self.window_minutes = env_int("VELOCITY_WINDOW_MINUTES", 5)

    def config(self):
        return {"max_transactions": self.max_txns, "window_minutes": self.window_minutes, "points": self.points}

    def evaluate(self, txn, ctx: RuleContext) -> RuleResult:
        now = as_utc(txn.timestamp)
        start = now - timedelta(minutes=self.window_minutes)
        in_window = sum(1 for h in ctx.history if start <= as_utc(h.timestamp) <= now)
        count = in_window + 1  # include the transaction being evaluated
        if count >= self.max_txns:
            return self.hit(
                f"{count} transactions within {self.window_minutes} minutes (limit is {self.max_txns})",
                count=count, window_minutes=self.window_minutes)
        return self.ok()
