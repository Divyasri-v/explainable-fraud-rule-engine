from app.config import env_float, env_int
from app.rules.base_rule import BaseRule, RuleContext, RuleResult
from app.utils import inr


class UnusualAmountRule(BaseRule):
    """Amount far above the customer's normal spending.

    Method:
      1. If the customer has >= AMOUNT_MIN_HISTORY prior "clean" transactions,
         compare the amount to  (historical average x AMOUNT_MULTIPLIER).
         Transactions that were themselves risky are excluded from the baseline
         so fraud cannot inflate what counts as "normal".
      2. Otherwise fall back to a fixed threshold (AMOUNT_FALLBACK_THRESHOLD).
    """
    name = "unusual_amount"
    display_name = "Unusual Transaction Amount"
    description = "Flags amounts far above the customer's historical average (fixed threshold if history is thin)."

    def __init__(self):
        self.points = env_int("AMOUNT_POINTS", 40)
        self.multiplier = env_float("AMOUNT_MULTIPLIER", 5)
        self.min_history = env_int("AMOUNT_MIN_HISTORY", 3)
        self.fallback = env_float("AMOUNT_FALLBACK_THRESHOLD", 50000)
        self.baseline_max_score = env_int("AMOUNT_BASELINE_MAX_SCORE", 30)

    def config(self):
        return {"multiplier": self.multiplier, "min_history": self.min_history,
                "fallback_threshold": self.fallback, "points": self.points}

    def evaluate(self, txn, ctx: RuleContext) -> RuleResult:
        amount = float(txn.amount)
        baseline = [float(h.amount) for h in ctx.history if (h.risk_score or 0) < self.baseline_max_score]

        if len(baseline) >= self.min_history:
            avg = sum(baseline) / len(baseline)
            if avg > 0 and amount > avg * self.multiplier:
                ratio = amount / avg
                return self.hit(
                    f"Amount {inr(amount)} is {ratio:.1f}× the customer's historical average of {inr(avg)} "
                    f"(limit {self.multiplier:g}×)", ratio=round(ratio, 2), average=round(avg, 2))
            return self.ok()

        if amount >= self.fallback:
            return self.hit(
                f"Amount {inr(amount)} exceeds the fixed threshold of {inr(self.fallback)} "
                f"(only {len(baseline)} prior transactions to compare with)", fallback=True)
        return self.ok()
