from dataclasses import dataclass, field
from typing import Optional, List
from domain import BookingPreference

# State: These represent where the user is in the conversation.
class State:
    GREET = "GREET"
    DISCLAIMER = "DISCLAIMER"
    INTENT = "INTENT" # What do you want to do?
    BOOK_TOPIC = "BOOK_TOPIC"
    CONFIRM_SLOT = "CONFIRM_SLOT"
    WAITLIST = "WAITLIST"
    CLOSE = "CLOSE"

@dataclass
class SessionContext:
    session_id: str
    state: str = State.GREET
    disclaimer_accepted: bool = False
    preference: BookingPreference = field(default_factory=BookingPreference)
    
    # We store the conversation history here too.
    history: List[str] = field(default_factory=list)
