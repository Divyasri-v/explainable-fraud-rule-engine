"""Common interface every fraud rule implements."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RuleResult:
    triggered: bool
    risk_points: int = 0
    reason: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class RuleContext:
    """Everything a rule may need besides the transaction itself.
    history: the customer's earlier transactions, newest first."""
    history: list = field(default_factory=list)


class BaseRule(ABC):
    name: str = ""            # unique machine name, stored in fraud_flags.rule_name
    display_name: str = ""    # shown in the UI
    description: str = ""     # one-line explanation shown in the UI
    points: int = 0           # risk points added when triggered

    @abstractmethod
    def evaluate(self, transaction, context: RuleContext) -> RuleResult:
        ...

    def config(self) -> dict:
        """Current tunable settings, exposed via GET /rules."""
        return {}

    def ok(self) -> RuleResult:
        return RuleResult(triggered=False)

    def hit(self, reason: str, **details) -> RuleResult:
        return RuleResult(triggered=True, risk_points=self.points, reason=reason, details=details)
