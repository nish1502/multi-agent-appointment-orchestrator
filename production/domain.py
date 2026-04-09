from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# 1. Topic Enum: This defines the only 5 specific things an advisor can talk about.
# Using an Enum (Enumeration) ensures we don't accidentally use a topic that doesn't exist.
class Topic(Enum):
    KYC_ONBOARDING = "KYC/Onboarding"
    SIP_MANDATES = "SIP/Mandates"
    STATEMENTS_TAX = "Statements/Tax Docs"
    WITHDRAWALS = "Withdrawals & Timelines"
    ACCOUNT_CHANGES = "Account Changes/Nominee"

# 2. TimeSlot: A simple data structure to hold a start and end time.
# We include a 'label_ist' which is the human-friendly version of the time in India Standard Time.
@dataclass
class TimeSlot:
    start_utc: datetime
    end_utc: datetime
    label_ist: str

# 3. BookingPreference: This holds what the user *wants* before we actually book it.
@dataclass
class BookingPreference:
    topic: Optional[Topic] = None
    preferred_date: Optional[str] = None  # e.g., "next Monday" or "2026-04-10"
    time_window: Optional[str] = None     # e.g., "morning", "afternoon"
