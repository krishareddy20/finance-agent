"""
GmailTool — OAuth2 Gmail wrapper.
Fetches unread emails and optionally sends messages.
"""

import os
import base64
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Read paths directly from environment here (not from config.py)
CREDS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE  = os.getenv("GMAIL_TOKEN_FILE", "token.json")


class GmailTool:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        print(f"  [Gmail] Using credentials file: {CREDS_FILE}")
        print(f"  [Gmail] File exists: {os.path.exists(CREDS_FILE)}")

        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def get_unread_emails(self, max_results: int = 25, query: str = "is:unread") -> list:
        """Return list of dicts with id, subject, sender, body."""
        results = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg_ref in messages:
            msg = self.service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            subject = headers.get("Subject", "")
            sender  = headers.get("From", "")
            body    = self._extract_body(msg["payload"])

            emails.append({
                "id":      msg_ref["id"],
                "subject": subject,
                "sender":  sender,
                "body":    body[:3000],
                "snippet": msg.get("snippet", ""),
            })

        return emails

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain-text body from MIME payload."""
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")

        if "parts" in payload:
            for part in payload["parts"]:
                text = self._extract_body(part)
                if text:
                    return text

        return payload.get("snippet", "")

    def mark_as_read(self, email_id: str):
        self.service.users().messages().modify(
            userId="me",
            id=email_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    def send_email(self, to: str, subject: str, body: str):
        import email.mime.text
        msg = email.mime.text.MIMEText(body)
        msg["to"]      = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        self.service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
