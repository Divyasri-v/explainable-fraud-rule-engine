"""Example new rule. To activate: copy this file to backend/app/rules/device_rule.py and restart.
Nothing else changes: not the engine, not main.py, not the API.

It flags very large round-number amounts that end in 000 above ₹10,000 (a stand-in for a
real device-fingerprint check, which would read a `device_id` column)."""
from app.config import env_int
from app.rules.base_rule import BaseRule, RuleContext, RuleResult
from app.utils import inr


class RoundAmountRule(BaseRule):
    name = "round_amount"
    display_name = "Suspicious Round Amount"
    description = "Flags large round-number amounts, which are common in card-testing and mule activity."

    def __init__(self):
        self.points = env_int("ROUND_AMOUNT_POINTS", 15)

    def evaluate(self, txn, ctx: RuleContext) -> RuleResult:
        amount = float(txn.amount)
        if amount >= 10000 and amount % 1000 == 0:
            return self.hit(f"{inr(amount)} is a large round-number amount")
        return self.ok()
