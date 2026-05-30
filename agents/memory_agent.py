"""
MemoryAgent — persists and learns from user decision history.
Uses OpenRouter free LLM for the periodic learning pass.
"""

import json
import re
from tools.llm_tool import call_llm


SYSTEM_PROMPT = """You are a personal finance assistant analysing a user's payment decisions.
Given a history of decisions, return updated user preferences as ONLY valid JSON (no markdown):
{
  "category_priorities": {"education": 8, "subscriptions": 5, ...},
  "trusted_merchants":   ["<merchant>", ...],
  "ignored_merchants":   ["<merchant>", ...]
}
Promote a merchant to trusted if approved 3+ times. Add to ignored if rejected 3+ times."""

TRUST_THRESHOLD  = 3
IGNORE_THRESHOLD = 3


class MemoryAgent:
    def __init__(self, storage_tool):
        self.storage = storage_tool

    def load(self) -> dict:
        return {
            "category_priorities": self.storage.load_memory("category_priorities", {
                "education":7,"utilities":9,"health":8,"subscriptions":5,
                "food":7,"travel":6,"entertainment":4,"shopping":5,"other":3,
            }),
            "trusted_merchants":  self.storage.load_memory("trusted_merchants", []),
            "ignored_merchants":  self.storage.load_memory("ignored_merchants", []),
            "approval_counts":    self.storage.load_memory("approval_counts", {}),
        }

    def record_decision(self, txn, decision: str, memory: dict):
        """Update approval/ignore counts and promote merchants if threshold reached."""
        merchant = txn.merchant.lower().strip()
        if not merchant:
            return

        counts = memory.get("approval_counts", {})

        if decision == "pay":
            counts[merchant] = counts.get(merchant, 0) + 1
            if counts[merchant] >= TRUST_THRESHOLD and merchant not in memory.get("trusted_merchants", []):
                memory.setdefault("trusted_merchants", []).append(merchant)
                print(f"  [Memory] '{merchant}' promoted to trusted merchant.")

        elif decision == "ignored":
            counts[merchant] = counts.get(merchant, 0) - 1
            if counts.get(merchant, 0) <= -IGNORE_THRESHOLD and merchant not in memory.get("ignored_merchants", []):
                memory.setdefault("ignored_merchants", []).append(merchant)
                print(f"  [Memory] '{merchant}' added to ignored merchants.")

        memory["approval_counts"] = counts
        self._save(memory)

    def learn_from_history(self, memory: dict) -> str:
        """
        Periodic learning pass: send last 50 decisions to LLM and get back
        updated category priorities and merchant lists.
        """
        txns = self.storage.get_all_transactions(limit=50)
        if not txns:
            return "No transactions to learn from."

        history_lines = "\n".join(
            f"- {t['description']} | ₹{t['amount']} | {t['category']} | "
            f"merchant={t['merchant']} | status={t['status']}"
            for t in txns
        )

        raw = call_llm(SYSTEM_PROMPT, f"Decision history:\n{history_lines}", max_tokens=400)

        try:
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            data  = json.loads(clean)
        except Exception:
            return "Learning pass — could not parse LLM response."

        memory["category_priorities"] = data.get("category_priorities", memory["category_priorities"])
        for m in data.get("trusted_merchants", []):
            if m not in memory["trusted_merchants"]:
                memory["trusted_merchants"].append(m)
        for m in data.get("ignored_merchants", []):
            if m not in memory["ignored_merchants"]:
                memory["ignored_merchants"].append(m)

        self._save(memory)
        return f"Learning complete. Trusted: {memory['trusted_merchants']}. Ignored: {memory['ignored_merchants']}."

    def _save(self, memory: dict):
        self.storage.save_memory("category_priorities", memory["category_priorities"])
        self.storage.save_memory("trusted_merchants",   memory["trusted_merchants"])
        self.storage.save_memory("ignored_merchants",   memory["ignored_merchants"])
        self.storage.save_memory("approval_counts",     memory.get("approval_counts", {}))
