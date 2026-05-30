"""
EmailAgent — scans Gmail for financial events and extracts Transaction objects.
Uses OpenRouter free LLM (no Anthropic SDK).
"""

import json
import re
from datetime import datetime

from tools.llm_tool import call_llm
from config import FINANCIAL_KEYWORDS, CATEGORIES
from models.transaction import Transaction


SYSTEM_PROMPT = """You are a financial data extractor. Given an email, extract payment/invoice details.
Return ONLY valid JSON with these exact keys (no extra text, no markdown):
{
  "amount": <number or null>,
  "merchant": "<string>",
  "category": "<education|subscriptions|utilities|health|food|travel|entertainment|shopping|other>",
  "deadline": "<YYYY-MM-DD or null>",
  "payment_link": "<url or null>",
  "importance": "<low|medium|high>",
  "is_financial": <true|false>
}
If the email is not about a payment or financial transaction, set is_financial to false."""


class EmailAgent:
    def __init__(self, gmail_tool):
        self.gmail = gmail_tool

    def scan_and_extract(self, max_emails: int = 25) -> list[Transaction]:
        print("  [Email] Fetching unread emails…")
        emails = self.gmail.get_unread_emails(max_results=max_emails)
        print(f"  [Email] Found {len(emails)} unread email(s).")

        transactions = []
        for email in emails:
            if not self._looks_financial(email):
                continue

            txn = self._extract_transaction(email)
            if txn:
                transactions.append(txn)
                self.gmail.mark_as_read(email["id"])

        print(f"  [Email] Extracted {len(transactions)} financial transaction(s).")
        return transactions

    def _looks_financial(self, email: dict) -> bool:
        text = (email["subject"] + " " + email["snippet"]).lower()
        return any(kw in text for kw in FINANCIAL_KEYWORDS)

    def _extract_transaction(self, email: dict) -> Transaction | None:
        user_prompt = (
            f"Subject: {email['subject']}\n"
            f"From: {email['sender']}\n\n"
            f"{email['body'][:2000]}"
        )

        raw = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=400)

        try:
            # Strip any accidental markdown fences
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            data  = json.loads(clean)
        except (json.JSONDecodeError, ValueError):
            print(f"  [Email] Could not parse LLM response for: {email['subject']}")
            return None

        if not data.get("is_financial") or not data.get("amount"):
            return None

        return Transaction(
            description  = email["subject"],
            amount       = float(data["amount"]),
            category     = data.get("category", "other"),
            merchant     = data.get("merchant", ""),
            deadline     = data.get("deadline"),
            payment_link = data.get("payment_link"),
            importance   = data.get("importance", "medium"),
            source       = "email",
            email_id     = email["id"],
        )
