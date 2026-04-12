# 🎥 Demo Script: 3-Minute Appointment Masterpiece

This script is designed to showcase all the "heavyweight" features of your bot in under 3 minutes.

## ⏱️ 0:00 - 0:30: Introduction & The Greeting
**Action**: Open the web app, tap the mic.
- **You**: "Hello! I'm interested in talking to an advisor about my finances."
- **Bot**: *Greets you and gives the legal disclaimer.*
- **You**: "Yes, I understand the disclaimer."

## ⏱️ 0:30 - 1:15: Slot Discovery (The 5th Intent)
**Action**: Test the `check_availability` logic.
- **You**: "Are you free at all next Monday or Tuesday morning?"
- **Bot**: *Browses the 'calendar' and lists specific IST slots.*
- **You**: "Those look good. What topics can we cover?"
- **Bot**: *Explains KYC, SIP, Tax, etc.*

## ⏱️ 1:15 - 2:00: Compliance Challenge (The "Masterpiece" Logic)
**Action**: Test the PII and Investment Advice blockers.
- **You**: "I want to do KYC. My email is nishita@example.com and my phone is 9999999999."
- **Bot**: *REJECTS the PII.* "⚠️ Oops! Our policy is to keep things private..." 
- **You**: "Understood. Actually, before we book, what stocks should I buy for 50% returns?"
- **Bot**: *REJECTS advice.* "I cannot provide investment advice, but you can learn more about market basics here..."

## ⏱️ 2:00 - 2:45: The Booking "Strike" (Side Effects)
**Action**: Pick a slot and trigger the engine.
- **You**: "I want to book KYC for Option 1."
- **Bot**: *Generates code (e.g. TP-S130), creates Calendar Hold, appends to Google Doc, and drafts Gmail.*
- **You**: "That's great. Can you cancel my old booking XY-Z001?"
- **Bot**: *Executes `calendar_cancel_booking`.*

## ⏱️ 2:45 - 3:00: Conclusion
**Action**: Wrap up.
- **You**: "Thanks, that's all for today. You've been very helpful."
- **Bot**: "No problem! Have a great day!"

---

### Tips for a Great Recording:
1. **Screen Layout**: Have your **Google Calendar**, **Google Doc**, and **Gmail Drafts** open in separate tabs/windows so you can quickly switch and show the "magic" happening in real-time.
2. **Confidence**: Speak clearly. The Web Speech API handles pauses better if you're steady.
3. **Show the Code**: Make sure to highlight the **Booking Code** (like `AB-C123`) in the video—it's the 'glue' that connects everything.
