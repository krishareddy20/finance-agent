"""
SMSAgent — parses SMS bank alerts into Transaction objects.
No LLM needed — uses regex patterns for speed and reliability.
"""

import re
from datetime import datetime
from models.transaction import Transaction
from config import CATEGORIES


DEBIT_PATTERNS = [
    r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)\s+(?:debited|spent|charged)",
    r"debited\s+(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)",
    r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)\s+(?:on|for|from)",
]
CREDIT_PATTERNS = [
    r"credited\s+(?:with\s+)?(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)",
    r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)\s+credited",
]


class SMSAgent:
    def __init__(self, sms_tool, test_mode: bool = False):
        self.sms_tool  = sms_tool
        self.test_mode = test_mode

    def scan_and_extract(self, days_back: int = 7) -> list[Transaction]:
        print("  [SMS] Fetching messages…")
        if self.test_mode:
            messages = self.sms_tool.get_sample_messages()
        else:
            messages = self.sms_tool.fetch_sms(days_back=days_back)

        print(f"  [SMS] {len(messages)} message(s) fetched.")
        txns = [t for msg in messages for t in self._parse(msg) if t]
        print(f"  [SMS] Extracted {len(txns)} transaction(s).")
        return txns

    def _parse(self, msg: dict) -> list[Transaction]:
        body   = msg["body"]
        sender = msg.get("sender", "")
        txns   = []

        # Check debit
        for pat in DEBIT_PATTERNS:
            m = re.search(pat, body, re.I)
            if m:
                amount   = float(m.group(1).replace(",", ""))
                merchant = self._extract_merchant(body)
                category = self._guess_category(body + " " + merchant)
                txns.append(Transaction(
                    description  = f"[DEBIT] {sender}: {body[:80]}",
                    amount       = amount,
                    category     = category,
                    merchant     = merchant,
                    source       = "sms",
                    status       = "paid",   # already debited
                ))
                break

        # Check credit
        for pat in CREDIT_PATTERNS:
            m = re.search(pat, body, re.I)
            if m:
                amount = float(m.group(1).replace(",", ""))
                txns.append(Transaction(
                    description  = f"[CREDIT] {sender}: {body[:80]}",
                    amount       = amount,
                    category     = "other",
                    merchant     = sender,
                    source       = "sms",
                    status       = "paid",
                ))
                break

        return txns

    def _extract_merchant(self, body: str) -> str:
        patterns = [
            r"(?:at|for|to|from)\s+([A-Z][A-Za-z0-9\s&'-]{2,25}?)(?:\.|,|\s+on|\s+via|$)",
            r"(?:Amazon|Swiggy|Zomato|Netflix|Spotify|Uber|Ola|Flipkart|Myntra|Steam|Udemy|Coursera)",
        ]
        for pat in patterns:
            m = re.search(pat, body, re.I)
            if m:
                return m.group(0).strip()
        return ""

    def _guess_category(self, text: str) -> str:
        text_lower = text.lower()
        for cat, keywords in CATEGORIES.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        return "other"

    def get_balance_from_sms(self):
        return self.sms_tool.get_balance_from_sms()
