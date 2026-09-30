from math import asin, cos, radians, sin, sqrt

from app.config import env_float, env_int
from app.rules.base_rule import BaseRule, RuleContext, RuleResult
from app.utils import as_utc

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance between two lat/lon points."""
    p1, p2 = radians(lat1), radians(lat2)
    dphi, dlmb = p2 - p1, radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


class ImpossibleGeographyRule(BaseRule):
    """Required travel speed between two consecutive transactions is unrealistic."""
    name = "impossible_geography"
    display_name = "Impossible Geographical Location"
    description = "Flags consecutive transactions whose distance/time implies unrealistic travel speed (Haversine)."

    def __init__(self):
        self.points = env_int("GEO_POINTS", 30)
        self.max_speed = env_float("GEO_MAX_SPEED_KMH", 900)
        self.min_distance = env_float("GEO_MIN_DISTANCE_KM", 50)

    def config(self):
        return {"max_speed_kmh": self.max_speed, "min_distance_km": self.min_distance, "points": self.points}

    def evaluate(self, txn, ctx: RuleContext) -> RuleResult:
        if not ctx.history:
            return self.ok()
        prev = ctx.history[0]  # most recent earlier transaction
        distance = haversine_km(prev.latitude, prev.longitude, txn.latitude, txn.longitude)
        seconds = max((as_utc(txn.timestamp) - as_utc(prev.timestamp)).total_seconds(), 1.0)
        speed = distance / (seconds / 3600)

        if distance >= self.min_distance and speed > self.max_speed:
            mins = seconds / 60
            gap = (f"{seconds:.0f} seconds" if seconds < 90 else
                   f"{mins:.0f} minutes" if mins < 120 else f"{mins / 60:.1f} hours")
            where = f" ({prev.city})" if prev.city else ""
            return self.hit(
                f"Previous transaction was {distance:,.0f} km away{where} only {gap} earlier — "
                f"required speed {speed:,.0f} km/h exceeds the {self.max_speed:g} km/h limit",
                distance_km=round(distance, 1), speed_kmh=round(speed, 1))
        return self.ok()
