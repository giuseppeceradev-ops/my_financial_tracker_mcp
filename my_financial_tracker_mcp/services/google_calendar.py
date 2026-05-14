import os
import logging
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES  = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar"
]
GOOGLE_CREDS = os.getenv("GOOGLE_CREDENTIALS_PATH")
BASE_URL = os.getenv("PUBLIC_BASE_URL")

class CalendarService:

    def __init__(self):
        self.service = self.build_calendar_service()


    def build_calendar_service(self):
        creds = None

        # 1. Se esiste già il token salvato, lo riusa
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        # 2. Se non esiste o non è valido → login OAuth
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDS,
                SCOPES 
            )

            creds = flow.run_local_server(port=0)

            # salva token per prossime volte
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        # 3. ritorna client Drive pronto
        return build("calendar", "v3", credentials=creds)

    def create_payment_event(
        self,
        title:str, 
        body:str, 
        amount, 
        due_date):
        
        event = {
            'summary': f'{title} - €{amount}',
            'description': body,
            'start': {
                'date': due_date,  # formato YYYY-MM-DD
            },
            'end': {
                'date': due_date,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1440},
                ],
            },
        }

        return self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()


    def remove_payment_event(
        self,
        event_id, 
        google_id
        ):
        self.service.events().delete(
            calendarId="primary",
            eventId=google_id
        ).execute()
        logger.info(f"Removed google event {event_id}")        
