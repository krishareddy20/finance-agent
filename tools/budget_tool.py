"""BudgetTool — convenience wrapper around StorageTool for budget calculations."""

from datetime import datetime
from models.budget import Budget


class BudgetTool:
    def __init__(self, storage):
        self.storage = storage

    def get_budget(self, category: str, month: str = None) -> Budget:
        if not month:
            month = datetime.now().strftime("%Y-%m")
        limits = self.storage.get_budgets()
        limit  = limits.get(category, 2000)
        spent  = self.storage.get_monthly_spent(category, month)
        return Budget(category=category, limit=limit, spent=spent)

    def get_all_budgets(self, month: str = None) -> dict:
        if not month:
            month = datetime.now().strftime("%Y-%m")
        limits = self.storage.get_budgets()
        return {
            cat: Budget(
                category=cat,
                limit=lim,
                spent=self.storage.get_monthly_spent(cat, month)
            )
            for cat, lim in limits.items()
        }

    def update_limit(self, category: str, new_limit: float):
        self.storage.update_budget(category, new_limit)
