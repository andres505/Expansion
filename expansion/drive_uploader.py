# expansion/drive_uploader.py

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


def get_drive_service():
    """
    Crea cliente de Google Drive usando JSON desde ENV.
    """
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON no definido")

    info = json.loads(raw)

    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=SCOPES
    )

    return build("drive", "v3", credentials=creds)


def upload_file_to_drive(
    *,
    local_path: str,
    drive_folder_id: str,
    filename: str | None = None,
    mimetype: str = "text/csv"
) -> dict:
    """
    Sube un archivo a Google Drive.

    Retorna:
    {
        file_id,
        name,
        webViewLink
    }
    """

    service = get_drive_service()

    if not os.path.exists(local_path):
        raise FileNotFoundError(local_path)

    file_metadata = {
        "name": filename or os.path.basename(local_path),
        "parents": [drive_folder_id],
    }

    media = MediaFileUpload(
        local_path,
        mimetype=mimetype,
        resumable=True
    )

    file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        )
        .execute()
    )

    return {
        "file_id": file["id"],
        "name": file["name"],
        "webViewLink": file["webViewLink"]
    }
