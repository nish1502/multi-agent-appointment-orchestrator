import os
import json
from groq import Groq
from typing import Optional, Dict, Any

# 1. Setup: Precise instructions for Llama (on Groq)
SYSTEM_PROMPT = """
You are an NLU (Natural Language Understanding) unit for an Advisor Appointment Scheduler.
Your job is to parse user text and output ONLY a valid JSON object.

Allowed Topics:
- KYC/Onboarding
- SIP/Mandates
- Statements/Tax Docs
- Withdrawals & Timelines
- Account Changes/Nominee

User Intents: book_new, reschedule, cancel, guidance, check_availability, unknown

Compliance Rules:
- If user asks for investment advice (e.g., "what should I buy?"), set 'investment_advice_requested' to true.
- If the user sounds very angry or upset, set 'is_urgent' to true.
- Do NOT extract phone numbers or emails.
- If the user provides a booking code (e.g. AB-C123), extract it into 'booking_code'.
- If the user asks about free slots or specific days, use 'check_availability'.

Output ONLY JSON in this format:
{
  "intent": "string",
  "topic": "string or null",
  "booking_code": "string or null",
  "date_info": "string or null",
  "investment_advice_requested": boolean,
  "is_urgent": boolean
}
"""

class NLUEngine:
    def __init__(self, api_key: Optional[str] = None):
        # Initialize Groq Client
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("❌ Error: GROQ_API_KEY is missing!")
            
        self.client = Groq(api_key=key)
        # We use a powerful Llama model from Groq
        self.model = "llama-3.3-70b-versatile"

    def parse(self, user_text: str) -> Dict[str, Any]:
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                model=self.model,
                # Groq supports forcing JSON output!
                response_format={"type": "json_object"}
            )
            
            result_text = chat_completion.choices[0].message.content
            return json.loads(result_text)
            
        except Exception as e:
            print(f"Groq NLU Error: {e}")
            return {
                "intent": "unknown", 
                "topic": None, 
                "date_info": None, 
                "investment_advice_requested": False,
                "is_urgent": False
            }
