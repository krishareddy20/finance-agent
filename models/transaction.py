"""Transaction data model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    description:  str
    amount:       float
    category:     str        = "other"
    merchant:     str        = ""
    deadline:     Optional[str] = None      # ISO date string or None
    payment_link: Optional[str] = None
    importance:   str        = "medium"     # low / medium / high
    source:       str        = "email"      # email / sms
    status:       str        = "pending"    # pending / paid / ignored / reminded
    email_id:     Optional[str] = None
    id:           Optional[int] = None
    created_at:   str        = field(default_factory=lambda: datetime.now().isoformat())
