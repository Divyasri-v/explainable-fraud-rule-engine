"""Rule auto-discovery.

Drop a new file in this package containing a BaseRule subclass and it is
picked up automatically. No engine code needs to change.
"""
import importlib
import inspect
import pkgutil

from app.config import get_settings
from app.rules.base_rule import BaseRule


def discover_rules() -> list:
    disabled = set(get_settings().disabled_rules)
    found = []
    for mod_info in pkgutil.iter_modules(__path__):
        if mod_info.name == "base_rule":
            continue
        module = importlib.import_module(f"{__name__}.{mod_info.name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (issubclass(cls, BaseRule) and not inspect.isabstract(cls)
                    and cls.__module__ == module.__name__):
                rule = cls()
                if rule.name not in disabled:
                    found.append(rule)
    return sorted(found, key=lambda r: r.name)
