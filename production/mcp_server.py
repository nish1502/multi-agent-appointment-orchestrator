from fastmcp import FastMCP
from datetime import datetime, timedelta
from google_calendar_auth import get_calendar_service, get_docs_service, get_gmail_service
import base64
from email.message import EmailMessage

# 1. Initialize the MCP Server
mcp = FastMCP("AdvisorService")

# YOUR REAL DOCUMENT ID (Replace this or create one at docs.new)
# Example: "1A2B3C4D5E..." from the URL of your Google Doc
LOG_DOC_ID = "1yKhHLuKH_o7VNMLWSKXHozTLnC4QqLTPy_emtyAPhSA" 
@mcp.tool()
def calendar_create_hold(start_time_iso: str, topic: str) -> str:
    """Creates a real Google Calendar event."""
    service = get_calendar_service()
    if not service: return "❌ Google Auth Error"
    
    event = {
        'summary': f'[TENTATIVE] {topic} Meeting',
        'description': f'Pre-booking for {topic}. (Code: GENERATING...)',
        'start': {'dateTime': start_time_iso, 'timeZone': 'UTC'},
        'end': {'dateTime': (datetime.fromisoformat(start_time_iso) + timedelta(minutes=30)).isoformat(), 'timeZone': 'UTC'},
    }
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ SUCCESS: GCal event created: {event.get('htmlLink')}"
    except Exception as e: return f"❌ GCal Error: {str(e)}"

@mcp.tool()
def docs_append_prebooking(booking_code: str, topic: str, timestamp: str) -> str:
    """Appends a new entry to the Advisor Pre-Bookings Google Doc."""
    service = get_docs_service()
    if not service: return "❌ Google Auth Error"

    text_to_append = f"\n[{timestamp}] Code: {booking_code} | Topic: {topic} | Status: TENTATIVE"
    
    requests = [{'insertText': {'location': {'index': 1}, 'text': text_to_append}}]
    
    try:
        service.documents().batchUpdate(documentId=LOG_DOC_ID, body={'requests': requests}).execute()
        return f"✅ SUCCESS: Logged in Google Doc (ID: ...{LOG_DOC_ID[-4:]})"
    except Exception as e:
        return f"⚠️ Doc Error: {str(e)}. (Make sure LOG_DOC_ID is correct and shared with your bot)."

@mcp.tool()
def calendar_cancel_booking(booking_code: str) -> str:
    """
    Finds and deletes the Google Calendar event associated with a booking code.
    """
    service = get_calendar_service()
    if not service: return "❌ Google Auth Error"

    try:
        # 1. Search for the event with this code
        # We search in the primary calendar for the text (booking code)
        events_result = service.events().list(calendarId='primary', q=booking_code).execute()
        events = events_result.get('items', [])

        if not events:
            return f"⚠️ Could not find any meeting with code {booking_code} on your calendar."

        # 2. Delete the first matching event found
        event_id = events[0]['id']
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return f"✅ SUCCESS: Meeting {booking_code} has been removed from your Google Calendar."
    except Exception as e:
        return f"❌ Cancellation Error: {str(e)}"

@mcp.tool()
def gmail_create_draft(recipient_email: str, subject: str, body: str) -> str:
    """Creates a real Gmail Draft."""
    service = get_gmail_service()
    if not service: return "❌ Google Auth Error"

    message = EmailMessage()
    message.set_content(body)
    message['To'] = recipient_email
    message['From'] = 'me'
    message['Subject'] = subject

    # Encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {'message': {'raw': encoded_message}}

    try:
        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        return f"✅ SUCCESS: Gmail Draft created (ID: {draft['id']}). Check your Drafts folder!"
    except Exception as e: return f"❌ Gmail Error: {str(e)}"
