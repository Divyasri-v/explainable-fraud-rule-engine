"""Generic rule engine. It knows nothing about individual rules."""
import logging
from dataclasses import dataclass, field

from app.config import Settings
from app.rules.base_rule import BaseRule, RuleContext, RuleResult

log = logging.getLogger("fraud.engine")


@dataclass
class EvaluationResult:
    score: int
    level: str
    flagged: bool
    results: list = field(default_factory=list)  # [(rule, RuleResult)] for every rule run

    @property
    def triggered(self):
        return [(rule, res) for rule, res in self.results if res.triggered]


class RuleEngine:
    def __init__(self, settings: Settings, rules=None):
        self.settings = settings
        self._rules: dict[str, BaseRule] = {}
        for rule in rules or []:
            self.register(rule)

    def register(self, rule: BaseRule):
        if not rule.name:
            raise ValueError("Rule must define a unique `name`")
        self._rules[rule.name] = rule

    def unregister(self, name: str):
        self._rules.pop(name, None)

    @property
    def rules(self) -> list:
        return list(self._rules.values())

    def level_for(self, score: int) -> str:
        s = self.settings
        if score >= s.critical_min:
            return "CRITICAL"
        if score >= s.high_min:
            return "HIGH"
        if score >= s.medium_min:
            return "MEDIUM"
        return "LOW"

    def evaluate(self, txn, context: RuleContext) -> EvaluationResult:
        results = []
        for rule in self._rules.values():
            try:
                res = rule.evaluate(txn, context)
            except Exception:  # one broken rule must never take down scoring
                log.exception("Rule %s failed; skipping", rule.name)
                res = RuleResult(triggered=False)
            results.append((rule, res))
        score = min(100, sum(r.risk_points for _, r in results if r.triggered))
        return EvaluationResult(score=score, level=self.level_for(score),
                                flagged=score >= self.settings.fraud_threshold, results=results)
