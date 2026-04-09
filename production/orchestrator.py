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
    # Check for PII like emails and phone numbers
    PII_REGEX = r"[\w\.-]+@[\w\.-]+\.\w+|(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"

    def __init__(self, nlu: NLUEngine):
        self.nlu = nlu

    def handle_message(self, user_text: str, ctx: SessionContext) -> str:
        # 1. Check for PII (Security)
        if re.search(self.PII_REGEX, user_text):
            return "⚠️ Oops! Our policy is to keep things private. Please don't share contact details yet. What topic would you like to discuss?"

        # 2. Get AI/NLU Results
        nlu_result = self.nlu.parse(user_text)
        intent = nlu_result.get("intent")
        
        # 3. Handle Secondary Intents (NEW IN PHASE 6)
        if intent == "cancel":
            code = nlu_result.get("booking_code")
            if not code:
                return "I'd be happy to help you cancel. Please provide your booking code (e.g., MJ-R257)."
            
            res = calendar_cancel_booking(code)
            ctx.state = State.CLOSE
            return f"{res}\nYour cancellation has also been logged for the advisor."

        elif intent == "check_availability":
            slots = MockCalendarService.find_two_slots(ctx.preference)
            if not slots:
                # PHASE 5: Waitlist logic
                ctx.state = State.WAITLIST
                return "I'm currently fully booked, but I can add you to my priority waitlist. Would you like that?"
            
            ctx.slots = slots
            slot_text = "\n".join([f"{i+1}. {s.label_ist}" for i, s in enumerate(slots)])
            return f"I have these windows open in IST:\n{slot_text}\n\nTo lock one in, could you tell me which topic you'd like to discuss? (KYC, SIP, etc.)"

        elif intent == "reschedule":
            return "To reschedule, please provide your booking code first so I can cancel the existing one, or just let me know which new slot you'd like!"

        elif intent == "guidance":
            if "kyc" in user_text.lower():
                return "For KYC, please have your PAN Card, Aadhaar Card, and a cancelled cheque ready. Would you like to book a slot for the onboarding?"
            return "Sure! For most meetings, bring your latest financial statements. Is there a specific topic you want guidance on?"

        # 4. Compliance Check (Investment Advice)
        if nlu_result.get("investment_advice_requested"):
            return "I cannot provide investment advice, but you can learn more about market basics here: https://www.investopedia.com/articles/basics/11/3-s-simple-investing.asp. Would you like to proceed with booking a slot for process-related questions?"
            
        # 5. Special Handling: Urgency/Angry User
        if nlu_result.get("is_urgent"):
            return "I understand you are upset. I will connect you to a human advisor immediately. Please hold."

        # 6. State Machine Transitions
        if ctx.state == State.GREET:
            ctx.state = State.DISCLAIMER
            return "Hello! I am your AI Advisor Scheduler. Before we begin, please note: I provide informational guidance and not investment advice. Do you understand?"

        if ctx.state == State.DISCLAIMER:
            if "yes" in user_text.lower() or "understand" in user_text.lower():
                ctx.disclaimer_accepted = True
                ctx.state = State.BOOK_TOPIC
                return "Great! What would you like to discuss with our advisor? (KYC, SIP, Tax, etc.)"
            else:
                return "I need your acknowledgment of the disclaimer. Do you understand?"

        if ctx.state == State.BOOK_TOPIC:
            topic_str = nlu_result.get("topic")
            
            # Map the string back to our Topic Enum
            for t in Topic:
                if t.value == topic_str:
                    ctx.preference.topic = t
                    break
            
            if ctx.preference.topic:
                # To test the waitlist, you can set force_full=True here!
                slots = MockCalendarService.find_two_slots(ctx.preference, force_full=False)
                
                if not slots:
                    ctx.state = State.WAITLIST
                    return f"I've noted your interest in {ctx.preference.topic.value}, but our advisor is currently fully booked. Would you like to be added to our Priority Waitlist? (Yes/No)"

                ctx.state = State.CONFIRM_SLOT
                response = f"I've noted that you're interested in {ctx.preference.topic.value}.\n"
                response += "I found these available slots (IST):\n"
                for i, s in enumerate(slots):
                    response += f"{i+1}. {s.label_ist}\n"
                response += "\nPlease type the number to pick a slot."
                return response
            else:
                return "I'm sorry, I couldn't identify the topic. We cover KYC, SIP, Tax, Withdrawals, and Account Changes. Which one do you need?"

        if ctx.state == State.WAITLIST:
            if "yes" in user_text.lower():
                # Side effect for waitlist
                booking_code = BookingCodeGenerator.generate()
                doc_res = docs_append_prebooking(booking_code, ctx.preference.topic.value, "WAITLIST-2026-04-09")
                ctx.state = State.CLOSE
                return f"✅ Done! You've been added to the Priority Waitlist. Your reference code is **{booking_code}**. We will alert you in IST as soon as a slot opens up."
            else:
                ctx.state = State.CLOSE
                return "No problem. Let me know if you change your mind. Have a great day!"

        if ctx.state == State.CONFIRM_SLOT:
            # ... (rest of slot selection logic)
            # Simple number parsing for beginner demo
            try:
                choice = int(re.search(r"\d", user_text).group())
                slots = MockCalendarService.find_two_slots(ctx.preference)
                if 1 <= choice <= len(slots):
                    selected_slot = slots[choice-1]
                    
                    # --- EXECUTE PHASE 4 SIDE EFFECTS ---
                    booking_code = BookingCodeGenerator.generate()
                    
                    # 1. Calendar Hold
                    # We store the booking code in the description so we can find it later to cancel!
                    cal_res = calendar_create_hold(selected_slot.start_utc.isoformat(), f"{ctx.preference.topic.value} (Code: {booking_code})")
                    
                    # 2. Log to Doc
                    doc_res = docs_append_prebooking(booking_code, ctx.preference.topic.value, "2026-04-09")
                    
                    # 3. Create Gmail Draft
                    email_body = f"Hello Advisor, a new pre-booking {booking_code} has been created for {ctx.preference.topic.value} at {selected_slot.label_ist}."
                    mail_res = gmail_create_draft("advisor@example.com", f"New Booking: {booking_code}", email_body)

                    ctx.state = State.CLOSE
                    
                    final_msg = f"🎉 **STRIKE! Booking Confirmed.**\n\nYour Booking Code is: **{booking_code}**\nSelected Slot: {selected_slot.label_ist}\n\n"
                    final_msg += "Internal Actions Taken:\n"
                    final_msg += f"- {cal_res}\n- {doc_res}\n- {mail_res}\n\n"
                    final_msg += "Anything else I can help with?"
                    return final_msg
                else:
                    return "Please choose a valid number (1 or 2)."
            except:
                return "I didn't catch a valid number. Please type 1 or 2."

        return "I'm not sure how to help. Let's start over!"
