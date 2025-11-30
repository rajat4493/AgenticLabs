from enum import Enum
from typing import Dict

_BAND_ALIASES: Dict[str, str] = {
    "simple": "low",
    "low": "low",
    "moderate": "medium",
    "medium": "medium",
    "complex": "high",
    "high": "high",
    "long_context": "high",
}


class RoutingBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def normalize(cls, band: str | None) -> "RoutingBand":
        if not band:
            return cls.MEDIUM
        alias = _BAND_ALIASES.get(band.lower())
        if alias:
            return cls(alias)
        try:
            return cls(band.lower())
        except ValueError:
            return cls.MEDIUM
