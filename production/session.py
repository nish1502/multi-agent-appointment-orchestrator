from dataclasses import dataclass, field
from typing import Optional, List
from production.domain import BookingPreference

# State: These represent where the user is in the conversation.
class State:
    GREET = "GREET"
    DISCLAIMER = "DISCLAIMER"
    INTENT = "INTENT" 
    BOOK_TOPIC = "BOOK_TOPIC"
    BOOK_TIME = "BOOK_TIME"
    CONFIRM = "CONFIRM"
    WAITLIST = "WAITLIST"
    CLOSE = "CLOSE"

from production.domain import TimeSlot

@dataclass
class SessionContext:
    session_id: str
    state: str = State.GREET
    disclaimer_accepted: bool = False
    preference: BookingPreference = field(default_factory=BookingPreference)
    slots: List[TimeSlot] = field(default_factory=list)
    proposed_slot: Optional[TimeSlot] = None
    history: List[str] = field(default_factory=list)
