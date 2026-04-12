import re
from production.session import State, SessionContext
from production.domain import Topic
from production.nlu_engine import NLUEngine

from production.booking_logic import BookingCodeGenerator, MockCalendarService
from production.mcp_server import calendar_create_hold, docs_append_prebooking, gmail_create_draft, calendar_cancel_booking

# A Fake AI for users who don't have an API key yet
class MockNLUEngine:
    def parse(self, text: str):
        text = text.lower()
        if "cancel" in text:
            # Try to extract something that looks like MJ-R257
            code_match = re.search(r"[A-Z]{2}-[A-Z]\d{3}", text.upper())
            return {"intent": "cancel", "booking_code": code_match.group() if code_match else None}
        if "advice" in text or "buy" in text:
            return {"intent": "guidance", "topic": None, "investment_advice_requested": True}
        if "kyc" in text or "onboarding" in text:
            return {"intent": "book_new", "topic": "KYC/Onboarding", "investment_advice_requested": False}
        if "sip" in text:
            return {"intent": "book_new", "topic": "SIP/Mandates", "investment_advice_requested": False}
        return {"intent": "book_new", "topic": None, "investment_advice_requested": False}

class Orchestrator:
    # Check for PII like emails and phone numbers (including variations like "at the rate")
    PII_REGEX = r"[\w\.-]+(@| at the rate | \[at\] )[\w\.-]+\.\w+|(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"

    def __init__(self, nlu: NLUEngine):
        self.nlu = nlu

    def handle_message(self, user_text: str, ctx: SessionContext) -> str:
        # 1. Privacy/Compliance Checks (Bypass everything)
        if re.search(self.PII_REGEX, user_text, re.IGNORECASE):
            return "I'm sorry, for your security, please do not share personal details like email or phone numbers on this call. I will give you a secure link at the end to provide those. Now, what topic can I help you with?"

        nlu_result = self.nlu.parse(user_text)
        intent = nlu_result.get("intent", "unknown")

        # 2. Compliance: Investment Advice (Highest Priority)
        if nlu_result.get("investment_advice_requested"):
            return "As an AI, I provide informational guidance and cannot offer specific investment advice. I recommend checking educational resources like [Investopedia](https://www.investopedia.com) or speaking with a certified planner."

        # 3. Handle GREET and DISCLAIMER first (Mandatory Funnel)
        if ctx.state == State.GREET:
            ctx.state = State.DISCLAIMER
            return "Hello! I am your AI Advisor Scheduler. Before we begin, please note: I provide informational guidance and not investment advice. Do you understand?"

        if ctx.state == State.DISCLAIMER:
            affirmations = ["yes", "understand", "agree", "ok", "sure", "yeah"]
            if any(word in user_text.lower() for word in affirmations):
                ctx.disclaimer_accepted = True
                ctx.state = State.BOOK_TOPIC
                return "Great! What would you like to discuss with our advisor? (KYC, SIP, Tax, Withdrawals, or Account Changes)"
            else:
                return "I'm sorry, I need you to confirm you understand the disclaimer before we can proceed. Do you understand?"

        # 4. Slot Filling: Topic and Time (Greedy extraction)
        # Always try to extract topic if we don't have it
        if not ctx.preference.topic:
            topic_str = nlu_result.get("topic")
            # Fallback manual check
            if not topic_str:
                for t in Topic:
                    if t.value.split("/")[0].lower() in user_text.lower():
                        topic_str = t.value
            
            if topic_str:
                for t in Topic:
                    if t.value.lower() == topic_str.lower() or topic_str.lower() in t.value.lower():
                        ctx.preference.topic = t
                        if ctx.state == State.BOOK_TOPIC: ctx.state = State.BOOK_TIME
                        break

        # Always try to extract intent-based info (Waitlist first)
        if ctx.state == State.WAITLIST:
            affirmations = ["yes", "yeah", "ok", "sure", "want"]
            if any(word in user_text.lower() for word in affirmations):
                booking_code = BookingCodeGenerator.generate()
                docs_append_prebooking(booking_code, ctx.preference.topic.value if ctx.preference.topic else "General", "WAITLIST-2026-04-09")
                ctx.state = State.CLOSE
                return f"✅ Done! You've been added to the Priority Waitlist. Your reference code is **{booking_code}**. We will alert you in IST as soon as a slot opens up."
            else:
                ctx.state = State.CLOSE
                return "No problem. Let me know if you change your mind. Have a great day!"

        # Handle specific Intents that might bypass states
        if intent == "cancel":
            return "To cancel, please provide your booking code. I can also help you book a new one if you like!"
        
        elif intent == "guidance":
            response = "For financial meetings, it's best to have your latest statements ready."
            if "tax" in user_text.lower(): response = "For tax, please bring your returns and Form 16."
            elif "kyc" in user_text.lower(): response = "For KYC, have your PAN and Aadhaar ready."
            return f"{response} Since we're ready, let's look for a slot. Which topic are we booking for?"

        # 5. Booking Logic (State-driven with Intent support)
        if ctx.state == State.BOOK_TOPIC and not ctx.preference.topic:
            return "Which topic would you like to discuss? (KYC, SIP, Tax, etc.)"

        # If we have a topic but no time, find slots
        if ctx.state == State.BOOK_TIME or (ctx.preference.topic and not ctx.proposed_slot):
            # Check if user already picked a slot from the list we gave (by number or time)
            if ctx.slots:
                picked_index = -1
                if "1" in user_text or "first" in user_text.lower(): picked_index = 0
                elif "2" in user_text or "second" in user_text.lower(): picked_index = 1
                
                # Manual time check
                for i, s in enumerate(ctx.slots):
                    # Check if the time (e.g. 4:30) appears in user text
                    time_part = s.label_ist.split(", ")[-1].split(" IST")[0] # e.g. "04:30 PM"
                    if time_part.replace("0", "") in user_text.replace("0", ""):
                        picked_index = i

                if picked_index != -1:
                    ctx.proposed_slot = ctx.slots[picked_index]
                    ctx.state = State.CONFIRM
                    ist_time = ctx.proposed_slot.label_ist
                    return f"Great choice. So we're booking **{ctx.preference.topic.value}** for **{ist_time}**. Shall I go ahead and confirm this for you?"

            # If no slot picked yet, offer them
            slots = MockCalendarService.find_two_slots(ctx.preference)
            if not slots:
                ctx.state = State.WAITLIST
                return "I'm currently fully booked for those dates, but I can add you to my priority waitlist. Would you like that?"
            
            ctx.slots = slots
            slot_text = "\n".join([f"{i+1}. {s.label_ist}" for i, s in enumerate(slots)])
            ctx.state = State.BOOK_TIME
            return f"I have these windows open in IST:\n{slot_text}\n\nPlease tell me which one works for you, or just say '1' or '2'."

        if ctx.state == State.CONFIRM:
            affirmations = ["yes", "confirm", "go ahead", "do it", "sure", "book"]
            if any(word in user_text.lower() for word in affirmations):
                booking_code = BookingCodeGenerator.generate()
                ist_time = ctx.proposed_slot.label_ist
                
                # MCP TRIPLE STRIKE
                # 1. Calendar
                title = f"Advisor Q&A - {ctx.preference.topic.value} - {booking_code}"
                calendar_create_hold(ctx.proposed_slot.start_utc.isoformat(), title)
                
                # 2. Docs
                docs_append_prebooking(booking_code, ctx.preference.topic.value, ist_time)
                
                # 3. Gmail Draft
                subject = f"New Appointment: {ctx.preference.topic.value} ({booking_code})"
                body = f"Hello, a new pre-booking has been created.\n\nTopic: {ctx.preference.topic.value}\nTime: {ist_time}\nCode: {booking_code}"
                gmail_create_draft("advisor@example.com", subject, body)
                
                ctx.state = State.CLOSE
                return f"✅ Confirmed! I've booked your **{ctx.preference.topic.value}** session for **{ist_time}**. Your booking code is **{booking_code}**. For your security, please visit [https://secure.advisor-portal.com/finish](https://secure.advisor-portal.com/finish) to provide your contact details. See you then!"
            else:
                return "No problem. Would you like to pick a different time or topic instead?"

        return "I'm not sure how to help. Should we try booking an appointment from the start?"
