"""
ReActAgent — Reason + Act agent loop for transaction decisions.

ReAct is a prompting pattern where the LLM alternates between:
  THOUGHT  → reasoning about what to do next
  ACTION   → calling a specific tool
  OBSERVE  → reading the tool's output
  ...repeat...
  ANSWER   → final decision

This is far more powerful than a single prompt because:
  1. The agent can gather multiple pieces of information before deciding
  2. It can detect when it needs more context and ask for it
  3. Each step is logged → full explainability (important for fintech)
  4. It's the same pattern used in LangChain, AutoGPT, and production agents

Tools available to the agent:
  - check_budget(category)      → current spend vs limit
  - get_similar_decisions(txn)  → RAG retrieval from vector memory
  - check_merchant_history(m)   → trust/ignore status of merchant
  - check_deadline(date)        → days until payment due
  - get_category_priority(cat)  → user's priority for this category

The agent runs up to MAX_STEPS steps then forces a final answer.
"""

import re
import json
from datetime import datetime, date

from tools.llm_tool import call_llm


MAX_STEPS = 5   # prevent infinite loops

SYSTEM_PROMPT = """You are a personal finance agent using the ReAct framework.
For each transaction, reason step by step using this EXACT format:

THOUGHT: <your reasoning about what information you need>
ACTION: <tool_name>(<argument>)
OBSERVE: <you will see the tool result here>

Repeat THOUGHT/ACTION/OBSERVE as needed (max 5 steps), then:
ANSWER: <pay|remind|ignore>
REASON: <one sentence explanation>
CONFIDENCE: <0.0-1.0>

Available tools:
- check_budget(category) — get current spend vs limit for a category
- get_similar_decisions(description) — find similar past transaction decisions
- check_merchant_history(merchant) — check if merchant is trusted or ignored
- check_deadline(date) — get days until due date
- get_category_priority(category) — get user's priority score for category

Rules:
- pay: important recurring bill, trusted merchant, within budget
- remind: large amount, far deadline, uncertain
- ignore: spam, promotional, already paid, ignored merchant"""


class ReActStep:
    """Represents one step in the ReAct loop."""
    def __init__(self, thought: str, action: str, observation: str):
        self.thought     = thought
        self.action      = action
        self.observation = observation
        self.timestamp   = datetime.now().isoformat()

    def to_dict(self):
        return {
            "thought":     self.thought,
            "action":      self.action,
            "observation": self.observation,
            "timestamp":   self.timestamp,
        }


class ReActAgent:
    """
    Runs a ReAct loop to decide what to do with a financial transaction.
    Each tool call is real — the agent reads actual budget/memory data.
    """

    def __init__(self, budget_tool, vector_memory, storage_tool):
        self.budget    = budget_tool
        self.vmem      = vector_memory
        self.storage   = storage_tool

    # ── Tool implementations ───────────────────────────────────────────────

    def _tool_check_budget(self, category: str) -> str:
        category = category.strip().lower()
        try:
            b = self.budget.get_budget(category)
            return (
                f"Category '{category}': spent ₹{b.spent:,.0f} of ₹{b.limit:,.0f} "
                f"({b.utilisation:.0%} used, ₹{b.remaining:,.0f} remaining)"
            )
        except Exception as e:
            return f"Budget data unavailable for '{category}': {e}"

    def _tool_get_similar_decisions(self, description: str) -> str:
        class FakeTxn:
            pass
        t = FakeTxn()
        t.description = description
        t.merchant    = ""
        t.category    = "other"
        t.amount      = 0
        return self.vmem.retrieve_similar(t, k=3)

    def _tool_check_merchant_history(self, merchant: str) -> str:
        merchant = merchant.strip().lower()
        trusted  = self.storage.load_memory("trusted_merchants", [])
        ignored  = self.storage.load_memory("ignored_merchants", [])
        counts   = self.storage.load_memory("approval_counts", {})

        if merchant in [m.lower() for m in trusted]:
            return f"'{merchant}' is a TRUSTED merchant — auto-approve."
        if merchant in [m.lower() for m in ignored]:
            return f"'{merchant}' is an IGNORED merchant — auto-reject."
        count = counts.get(merchant, 0)
        return f"'{merchant}' is unknown. Past approval count: {count}."

    def _tool_check_deadline(self, date_str: str) -> str:
        if not date_str or date_str.lower() in ("none", "null", ""):
            return "No deadline specified."
        try:
            due  = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d").date()
            days = (due - date.today()).days
            if days < 0:
                return f"OVERDUE by {abs(days)} days!"
            if days == 0:
                return "Due TODAY — urgent!"
            if days <= 3:
                return f"Due in {days} days — very soon."
            if days <= 7:
                return f"Due in {days} days — this week."
            return f"Due in {days} days — not urgent."
        except ValueError:
            return f"Could not parse deadline: '{date_str}'"

    def _tool_get_category_priority(self, category: str) -> str:
        category = category.strip().lower()
        prios    = self.storage.load_memory("category_priorities", {})
        default  = {"utilities": 9, "health": 8, "education": 7, "food": 7,
                    "travel": 6, "subscriptions": 5, "shopping": 5,
                    "entertainment": 4, "other": 3}
        priority = prios.get(category, default.get(category, 5))
        return f"Category '{category}' priority: {priority}/10"

    # ── Tool dispatcher ────────────────────────────────────────────────────

    def _dispatch_tool(self, action_str: str) -> str:
        """Parse ACTION: tool_name(arg) and call the right method."""
        match = re.match(r"(\w+)\((.*)?\)", action_str.strip())
        if not match:
            return f"Unknown action format: '{action_str}'"

        tool_name = match.group(1).strip()
        argument  = match.group(2).strip().strip("'\"") if match.group(2) else ""

        tools = {
            "check_budget":             self._tool_check_budget,
            "get_similar_decisions":    self._tool_get_similar_decisions,
            "check_merchant_history":   self._tool_check_merchant_history,
            "check_deadline":           self._tool_check_deadline,
            "get_category_priority":    self._tool_get_category_priority,
        }

        fn = tools.get(tool_name)
        if fn:
            return fn(argument)
        return f"Tool '{tool_name}' not found. Available: {list(tools.keys())}"

    # ── Main ReAct loop ────────────────────────────────────────────────────

    def decide(self, txn) -> tuple[str, str, float, list]:
        """
        Run the ReAct loop for a transaction.
        Returns (decision, reasoning, confidence, steps_log).
        """
        steps: list[ReActStep] = []

        # Build initial prompt
        user_prompt = (
            f"Transaction to evaluate:\n"
            f"  Description : {txn.description}\n"
            f"  Amount      : ₹{txn.amount}\n"
            f"  Category    : {txn.category}\n"
            f"  Merchant    : {txn.merchant or 'unknown'}\n"
            f"  Deadline    : {txn.deadline or 'not specified'}\n"
            f"  Importance  : {txn.importance}\n\n"
            f"Begin your ReAct reasoning:"
        )

        conversation = user_prompt
        final_decision   = "remind"
        final_reasoning  = "ReAct loop did not complete."
        final_confidence = 0.5

        for step_num in range(MAX_STEPS):
            response = call_llm(SYSTEM_PROMPT, conversation, max_tokens=600)

            if "__LLM_UNAVAILABLE__" in response:
                # Graceful fallback
                final_decision   = "remind"
                final_reasoning  = "LLM unavailable — defaulting to remind."
                final_confidence = 0.4
                break

            # Check if we have a final ANSWER
            if "ANSWER:" in response:
                answer_match     = re.search(r"ANSWER:\s*(pay|remind|ignore)", response, re.I)
                reason_match     = re.search(r"REASON:\s*(.+)",                response)
                confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)",        response)

                final_decision   = answer_match.group(1).lower()     if answer_match     else "remind"
                final_reasoning  = reason_match.group(1).strip()     if reason_match     else "No reason given."
                final_confidence = float(confidence_match.group(1))  if confidence_match else 0.7
                break

            # Parse THOUGHT / ACTION / OBSERVE
            thought_match = re.search(r"THOUGHT:\s*(.+?)(?=ACTION:|$)", response, re.S)
            action_match  = re.search(r"ACTION:\s*(.+?)(?=OBSERVE:|THOUGHT:|ANSWER:|$)", response, re.S)

            thought = thought_match.group(1).strip() if thought_match else ""
            action  = action_match.group(1).strip()  if action_match  else ""

            if not action:
                # LLM didn't follow format — force an answer
                break

            # Execute the tool
            observation = self._dispatch_tool(action)

            step = ReActStep(thought, action, observation)
            steps.append(step)

            # Append to conversation so LLM sees tool results
            conversation += (
                f"\nTHOUGHT: {thought}"
                f"\nACTION: {action}"
                f"\nOBSERVE: {observation}"
            )

        return final_decision, final_reasoning, final_confidence, steps
