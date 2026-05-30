"""User-behaviour memory model."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Memory:
    category_priorities: Dict[str, int] = field(default_factory=lambda: {
        "education":      8,
        "utilities":      9,
        "health":         8,
        "subscriptions":  5,
        "food":           7,
        "travel":         6,
        "entertainment":  4,
        "shopping":       5,
        "other":          3,
    })
    trusted_merchants: List[str] = field(default_factory=list)
    ignored_merchants: List[str] = field(default_factory=list)
    approval_counts:  Dict[str, int] = field(default_factory=dict)   # merchant → approve count
