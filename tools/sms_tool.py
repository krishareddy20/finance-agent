"""
SMSTool — reads SMS via ADB (Android Debug Bridge).
Requires: phone connected via USB + USB debugging enabled.
"""

import subprocess
import re
from datetime import datetime, timedelta


BANK_SMS_PATTERNS = [
    r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)",   # amount
    r"Avl Bal:?\s*(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)",   # balance
]


class SMSTool:
    def fetch_sms(self, days_back: int = 7) -> list:
        """Pull SMS messages from connected Android phone via ADB."""
        try:
            result = subprocess.run(
                ["adb", "shell", "content", "query",
                 "--uri", "content://sms/inbox",
                 "--projection", "address,date,body"],
                capture_output=True, text=True, timeout=15
            )
            return self._parse_adb_output(result.stdout, days_back)
        except FileNotFoundError:
            raise RuntimeError("ADB not found. Install Android Platform Tools and connect your phone.")

    def _parse_adb_output(self, raw: str, days_back: int) -> list:
        messages = []
        cutoff = datetime.now() - timedelta(days=days_back)
        for block in raw.strip().split("Row:"):
            if not block.strip():
                continue
            address = re.search(r"address=([^,]+)", block)
            date_ms = re.search(r"date=(\d+)", block)
            body    = re.search(r"body=(.+)", block, re.DOTALL)
            if not (address and date_ms and body):
                continue
            ts = datetime.fromtimestamp(int(date_ms.group(1)) / 1000)
            if ts < cutoff:
                continue
            messages.append({
                "sender": address.group(1).strip(),
                "date":   ts.isoformat(),
                "body":   body.group(1).strip(),
            })
        return messages

    def get_sample_messages(self) -> list:
        """Sample messages for test mode — no phone needed."""
        return [
            {"sender": "HDFCBK",  "date": datetime.now().isoformat(),
             "body": "Dear Customer, Rs.1,299.00 debited from A/c XX1234 on 19-Apr for Amazon. Avl Bal: Rs.18,450.50"},
            {"sender": "ICICIBK", "date": datetime.now().isoformat(),
             "body": "INR 499.00 debited from your account for Netflix subscription. Available Balance: INR 12,300.00"},
            {"sender": "SBIINB",  "date": datetime.now().isoformat(),
             "body": "Your A/c XXXX5678 is credited with Rs.25,000.00 on 18-Apr-26. Avl Bal Rs.37,300.00"},
        ]

    def get_balance_from_sms(self) -> dict | None:
        """Try to extract latest bank balance from recent SMS."""
        try:
            msgs = self.fetch_sms(days_back=3)
        except Exception:
            msgs = self.get_sample_messages()

        for msg in msgs:
            bal_match = re.search(r"(?:Avl Bal|Available Balance):?\s*(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)", msg["body"], re.I)
            if bal_match:
                balance = float(bal_match.group(1).replace(",", ""))
                return {"sender": msg["sender"], "balance": balance, "date": msg["date"]}
        return None
