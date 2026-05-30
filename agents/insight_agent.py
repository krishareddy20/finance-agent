"""
InsightAgent — spending reports, dashboard, and savings tips.
Uses OpenRouter free LLM.
"""

from datetime import datetime
from tools.llm_tool import call_llm


REPORT_SYSTEM = """You are a personal finance advisor. Given a user's monthly spending summary,
write a concise, friendly report (max 200 words) with:
1. Overall verdict (on track / over budget)
2. Top 2-3 spending categories worth noting
3. One actionable savings tip
Use plain text, no markdown headers."""

TIPS_SYSTEM = """You are a personal finance advisor. Given overspent categories,
suggest 3 specific, practical savings tips in plain numbered list format."""


class InsightAgent:
    def __init__(self, storage_tool, budget_tool):
        self.storage = storage_tool
        self.budget  = budget_tool

    # ------------------------------------------------------------------
    # Dashboard (terminal)
    # ------------------------------------------------------------------
    def print_dashboard(self):
        month   = datetime.now().strftime("%Y-%m")
        budgets = self.budget.get_all_budgets(month)

        print("\n  ┌─ SPENDING DASHBOARD ─────────────────────────────────")
        print(f"  │  Month: {month}")
        print(f"  │  {'Category':<16} {'Spent':>8}  {'Limit':>8}  {'Used':>6}")
        print(f"  │  {'─'*46}")
        for cat, b in sorted(budgets.items()):
            bar   = "█" * int(b.utilisation * 10) + "░" * (10 - int(b.utilisation * 10))
            flag  = " ⚠" if b.utilisation >= 0.8 else ""
            print(f"  │  {cat:<16} ₹{b.spent:>7,.0f}  ₹{b.limit:>7,.0f}  {bar}{flag}")
        total_spent = sum(b.spent for b in budgets.values())
        total_limit = sum(b.limit for b in budgets.values())
        print(f"  │  {'─'*46}")
        print(f"  │  {'TOTAL':<16} ₹{total_spent:>7,.0f}  ₹{total_limit:>7,.0f}")
        print("  └──────────────────────────────────────────────────────\n")

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    def generate_report(self, period: str = "monthly") -> str:
        month   = datetime.now().strftime("%Y-%m")
        budgets = self.budget.get_all_budgets(month)

        summary_lines = "\n".join(
            f"{cat}: spent ₹{b.spent:.0f} of ₹{b.limit:.0f} ({b.utilisation:.0%})"
            for cat, b in budgets.items()
        )
        total_spent = sum(b.spent for b in budgets.values())
        total_limit = sum(b.limit for b in budgets.values())
        summary_lines += f"\nTotal: ₹{total_spent:.0f} of ₹{total_limit:.0f}"

        user_prompt = f"{period.capitalize()} spending for {month}:\n{summary_lines}"
        report = call_llm(REPORT_SYSTEM, user_prompt, max_tokens=300)
        return f"\n=== {period.upper()} REPORT — {month} ===\n{report}\n"

    def savings_recommendation(self) -> str:
        month   = datetime.now().strftime("%Y-%m")
        budgets = self.budget.get_all_budgets(month)
        over    = [f"{cat} (₹{b.spent:.0f} / ₹{b.limit:.0f})"
                   for cat, b in budgets.items() if b.utilisation >= 0.8]

        if not over:
            return "All categories are within budget. Keep it up!"

        user_prompt = "Over-budget categories:\n" + "\n".join(over)
        return call_llm(TIPS_SYSTEM, user_prompt, max_tokens=200)
