"""
DecisionAgent — upgraded to use all 5 enhancements:
  1. ML classifier for fast category prediction
  2. Vector memory (RAG) for semantic context retrieval
  3. ReAct agent loop for multi-step reasoning
  4. Falls back gracefully if any component is unavailable
"""

import json
import re
from datetime import datetime

from tools.llm_tool import call_llm
from config import AUTO_APPROVE_BELOW, REQUIRE_APPROVAL_ABOVE, CRITICAL_PAYMENT_THRESHOLD


FALLBACK_SYSTEM = """You are a personal finance assistant. Given a transaction and budget,
return ONLY valid JSON: {"decision":"pay|remind|ignore","reasoning":"one sentence","confidence":0.0-1.0}"""


class DecisionAgent:
    def __init__(self, budget_tool, vector_memory=None, classifier=None, storage_tool=None):
        self.budget_tool  = budget_tool
        self.vector_memory = vector_memory
        self.classifier    = classifier
        self.storage       = storage_tool

        # Try to initialise ReAct agent
        self._react = None
        if vector_memory and storage_tool:
            try:
                from core.react_agent import ReActAgent
                self._react = ReActAgent(budget_tool, vector_memory, storage_tool)
                print("  [Decision] ReAct agent ready.")
            except Exception as e:
                print(f"  [Decision] ReAct not available: {e}")

    def evaluate(self, txn, memory: dict) -> tuple[str, str, float]:
        """
        Full pipeline:
          1. Check trusted/ignored merchant (instant)
          2. ML classifier validates/corrects category
          3. ReAct agent reasons through the decision
          4. Falls back to simple LLM prompt if ReAct fails
        """

        # ── Step 1: Fast merchant check ────────────────────────────────
        merchant_lower = txn.merchant.lower().strip()
        if merchant_lower in [m.lower() for m in memory.get("trusted_merchants", [])]:
            return "pay", "Trusted merchant — auto-approved.", 0.95
        if merchant_lower in [m.lower() for m in memory.get("ignored_merchants", [])]:
            return "ignore", "Previously ignored merchant.", 0.90

        # ── Step 2: ML classifier validates category ───────────────────
        if self.classifier:
            try:
                ml_cat, ml_conf = self.classifier.predict(txn.description, txn.merchant)
                if ml_conf > 0.7 and ml_cat != txn.category:
                    print(f"  [Classifier] Corrected category: {txn.category} → {ml_cat} ({ml_conf:.0%})")
                    txn.category = ml_cat
            except Exception:
                pass

        # ── Step 3: ReAct multi-step reasoning ─────────────────────────
        if self._react:
            try:
                decision, reasoning, confidence, steps = self._react.decide(txn)
                if steps:
                    print(f"  [ReAct] {len(steps)} reasoning steps taken.")

                # Store decision in vector memory for future RAG retrieval
                if self.vector_memory:
                    self.vector_memory.store_decision(txn, decision, reasoning)

                return decision, reasoning, confidence
            except Exception as e:
                print(f"  [ReAct] Failed: {e} — falling back to simple LLM.")

        # ── Step 4: Simple LLM fallback ────────────────────────────────
        return self._simple_llm_decide(txn, memory)

    def _simple_llm_decide(self, txn, memory: dict) -> tuple[str, str, float]:
        budgets = self.budget_tool.get_all_budgets()
        budget_lines = "\n".join(
            f"  {cat}: spent ₹{b.spent:.0f}/₹{b.limit:.0f} ({b.utilisation:.0%})"
            for cat, b in budgets.items()
        )

        # Add RAG context if available
        rag_context = ""
        if self.vector_memory:
            rag_context = "\n\nSimilar past decisions:\n" + self.vector_memory.retrieve_similar(txn)

        user_prompt = (
            f"Transaction: {txn.description}\n"
            f"Amount: ₹{txn.amount}  Category: {txn.category}  "
            f"Merchant: {txn.merchant}  Deadline: {txn.deadline}\n\n"
            f"Budget:\n{budget_lines}{rag_context}"
        )

        raw = call_llm(FALLBACK_SYSTEM, user_prompt, max_tokens=200)
        try:
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            data  = json.loads(clean)
            return data["decision"], data["reasoning"], float(data["confidence"])
        except Exception:
            return "remind", "Could not parse LLM response.", 0.5

    def requires_approval(self, txn) -> bool:
        return txn.amount >= REQUIRE_APPROVAL_ABOVE

    def is_over_budget(self, txn) -> bool:
        budget = self.budget_tool.get_budget(txn.category)
        if budget.limit == 0:
            return False
        return (budget.spent + txn.amount) / budget.limit >= CRITICAL_PAYMENT_THRESHOLD
