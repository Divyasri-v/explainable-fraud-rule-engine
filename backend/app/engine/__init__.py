from functools import lru_cache

from app.config import get_settings
from app.engine.rule_engine import RuleEngine
from app.rules import discover_rules


@lru_cache
def get_engine() -> RuleEngine:
    """Engine pre-loaded with every rule discovered in app/rules/."""
    return RuleEngine(get_settings(), discover_rules())
