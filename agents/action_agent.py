"""
ActionAgent — handles approvals, calendar reminders, and status updates.
"""


class ActionAgent:
    def __init__(self, calendar_tool, gmail_tool, storage_tool, user_email: str):
        self.calendar = calendar_tool
        self.gmail    = gmail_tool
        self.storage  = storage_tool
        self.user_email = user_email

    # ------------------------------------------------------------------
    # Approval
    # ------------------------------------------------------------------
    def request_approval(self, txn, reasoning: str) -> str:
        """
        Print transaction details in terminal and ask user y/n/remind.
        Returns 'y', 'n', or 'remind'.
        """
        print(f"\n  ┌─ APPROVAL REQUIRED ────────────────────────────────")
        print(f"  │  Description : {txn.description}")
        print(f"  │  Amount      : ₹{txn.amount:,.2f}")
        print(f"  │  Category    : {txn.category}")
        print(f"  │  Merchant    : {txn.merchant or 'unknown'}")
        print(f"  │  Deadline    : {txn.deadline or 'not specified'}")
        if txn.payment_link:
            print(f"  │  Link        : {txn.payment_link}")
        print(f"  │  Reason      : {reasoning}")
        print(f"  └────────────────────────────────────────────────────")

        while True:
            choice = input("  Pay? [y / n / remind]: ").strip().lower()
            if choice in ("y", "n", "remind"):
                return choice
            print("  Please enter y, n, or remind.")

    # ------------------------------------------------------------------
    # Status updates
    # ------------------------------------------------------------------
    def mark_paid(self, txn):
        if txn.id:
            self.storage.update_status(txn.id, "paid")

    def mark_ignored(self, txn):
        if txn.id:
            self.storage.update_status(txn.id, "ignored")

    def schedule_reminder(self, txn, save: bool = True):
        title       = f"Pay: {txn.description} — ₹{txn.amount:,.2f}"
        description = (
            f"Merchant: {txn.merchant}\n"
            f"Amount: ₹{txn.amount:,.2f}\n"
            + (f"Link: {txn.payment_link}" if txn.payment_link else "")
        )
        try:
            link = self.calendar.create_reminder(title, description, txn.deadline)
            print(f"  Calendar reminder created: {link}")
        except Exception as e:
            print(f"  Could not create calendar reminder: {e}")

        if save and txn.id:
            self.storage.update_status(txn.id, "reminded")

    # ------------------------------------------------------------------
    # Email summary
    # ------------------------------------------------------------------
    def send_summary_email(self, subject: str, body: str):
        try:
            self.gmail.send_email(self.user_email, subject, body)
            print(f"  Summary email sent to {self.user_email}.")
        except Exception as e:
            print(f"  Could not send summary email: {e}")
