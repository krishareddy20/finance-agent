"""
CalendarTool — Google Calendar OAuth2 wrapper.
Creates payment-reminder events with email + popup notifications.
"""

import os
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarTool:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(GMAIL_TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
            except Exception:
                pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(GMAIL_TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)

    def create_reminder(self, title: str, description: str, due_date: str) -> str:
        """
        Create an all-day event with reminders.
        due_date: ISO date string (YYYY-MM-DD) or None (defaults to tomorrow).
        Returns the event URL.
        """
        if due_date:
            date_str = due_date[:10]
        else:
            date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        event = {
            "summary":     title,
            "description": description,
            "start": {"date": date_str},
            "end":   {"date": date_str},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 24 * 60},
                    {"method": "popup",  "minutes": 60},
                ],
            },
        }

        created = self.service.events().insert(calendarId="primary", body=event).execute()
        return created.get("htmlLink", "")
