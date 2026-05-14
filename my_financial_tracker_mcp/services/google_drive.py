from PIL.Image import logger
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DRIVE_CALENDAR_SCOPES  = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar"
]
GMAIL_CREDS = os.getenv("GMAIL_CREDENTIALS_PATH")


class DriveService:
    def __init__(self):
        self.drive_service = self._build_drive_service()

    def upload_file(
        self,
        file_path, 
        folder_id=None, 
        date=None):
        if date is None:
            date = datetime.today()

        day_folder_id = self._ensure_date_path(folder_id, date)


        file_metadata = {
            "name": file_path.split("/")[-1],
        }

        if day_folder_id:
            file_metadata["parents"] = [day_folder_id]

        media = MediaFileUpload(file_path, resumable=True)

        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink"
        ).execute()

        logger.info(f"Uploaded file ({file_path})")

        return file["webViewLink"]


    def _get_or_create_folder(
        self,
        name, 
        parent_id):
        query = (
            f"name='{name}' "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and '{parent_id}' in parents "
            f"and trashed=false"
        )

        response = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
        ).execute()

        files = response.get('files', [])

        if files:
            return files[0]['id']

        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }

        folder = self.drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()

        return folder['id']

    def _ensure_date_path(
        self,
        base_folder_id, 
        date: datetime):
        year = str(date.year)
        month = f"{date.month:02d}"
        day = f"{date.day:02d}"

        year_id = self._get_or_create_folder(year, base_folder_id)
        month_id = self._get_or_create_folder(month, year_id)
        day_id = self._get_or_create_folder(day, month_id)

        return day_id

    def _build_drive_service(
        self
    ):
        creds = None

        # 1. Se esiste già il token salvato, lo riusa
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        # 2. Se non esiste o non è valido → login OAuth
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDS,
                DRIVE_CALENDAR_SCOPES 
            )

            creds = flow.run_local_server(port=0)

            # salva token per prossime volte
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        # 3. ritorna client Drive pronto
        return build("drive", "v3", credentials=creds)