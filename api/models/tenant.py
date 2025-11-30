from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Tenant:
    id: str
    name: str
    allowed_models: List[str] = field(default_factory=list)
