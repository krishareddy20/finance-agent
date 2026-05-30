"""Budget model."""
from dataclasses import dataclass


@dataclass
class Budget:
    category: str
    limit:    float
    spent:    float = 0.0

    @property
    def remaining(self) -> float:
        return max(0.0, self.limit - self.spent)

    @property
    def utilisation(self) -> float:
        return self.spent / self.limit if self.limit > 0 else 0.0
