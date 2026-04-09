import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Expanded Scopes: Calendar, Docs (Append), and Gmail (Compose Drafts)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose'
]

def get_calendar_service():
    """Authenticates and returns the Google Calendar service object."""
    creds = authenticate()
    return build('calendar', 'v3', credentials=creds) if creds else None

def get_docs_service():
    """Authenticates and returns the Google Docs service object."""
    creds = authenticate()
    return build('docs', 'v1', credentials=creds) if creds else None

def get_gmail_service():
    """Authenticates and returns the Gmail service object."""
    creds = authenticate()
    return build('gmail', 'v1', credentials=creds) if creds else None

def authenticate():
    """Handles the OAuth2 flow and returns credentials."""
    creds = None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(base_dir, 'token.json')
    creds_path = os.path.join(base_dir, 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print(f"❌ ERROR: credentials.json not found at {creds_path}!")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds
