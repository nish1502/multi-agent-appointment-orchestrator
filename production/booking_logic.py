import random
import string
from datetime import datetime, timedelta
from typing import List
from domain import Topic, TimeSlot, BookingPreference

# 1. BookingCodeGenerator: This creates a unique ID for every appointment.
# Pattern: [A-Z]{2}-[A-Z][0-9]{3} (e.g., NL-A742)
class BookingCodeGenerator:
    @staticmethod
    def generate() -> str:
        # First 2 letters (random uppercase)
        prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
        # 1 random letter
        mid = random.choice(string.ascii_uppercase)
        # 3 random numbers
        suffix = ''.join(random.choices(string.digits, k=3))
        
        return f"{prefix}-{mid}{suffix}"

from google_calendar_auth import get_calendar_service
from datetime import datetime, timedelta, time

class MockCalendarService:
    @staticmethod
    def find_two_slots(preference: BookingPreference, force_full: bool = False) -> List[TimeSlot]:
        if force_full: return []
        
        service = get_calendar_service()
        if not service: return []

        now = datetime.utcnow()
        # Search for the next 7 days
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=7)).isoformat() + 'Z'

        try:
            # 1. Get busy times from Google
            body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": "primary"}]
            }
            events_result = service.freebusy().query(body=body).execute()
            busy_times = events_result.get('calendars', {}).get('primary', {}).get('busy', [])

            # 2. Logic to find gaps (Simplification: look for 10am-5pm items)
            # For this demo, we'll return the first 2 available "top-of-hour" slots
            available_slots = []
            test_date = now + timedelta(days=1)
            
            while len(available_slots) < 2 and test_date < (now + timedelta(days=7)):
                # Try 10 AM, 11 AM, 2 PM, 3 PM
                for hour in [10, 11, 14, 15]:
                    candidate_start = datetime.combine(test_date.date(), time(hour, 0))
                    candidate_end = candidate_start + timedelta(minutes=30)
                    
                    # Check if this candidate overlaps with any busy time
                    is_busy = False
                    for b in busy_times:
                        b_start = datetime.fromisoformat(b['start'].replace('Z', ''))
                        b_end = datetime.fromisoformat(b['end'].replace('Z', ''))
                        if (candidate_start < b_end and candidate_end > b_start):
                            is_busy = True
                            break
                    
                    if not is_busy:
                        # Convert to IST label for the UI
                        ist_offset = timedelta(hours=5, minutes=30)
                        ist_start = candidate_start + ist_offset
                        label = ist_start.strftime("%A, %d %B %Y, %I:%M %p IST")
                        
                        available_slots.append(TimeSlot(
                            start_utc=candidate_start,
                            end_utc=candidate_end,
                            label_ist=label
                        ))
                        if len(available_slots) >= 2: break
                test_date += timedelta(days=1)

            return available_slots
        except Exception as e:
            print(f"❌ Calendar Error: {e}")
            return []
