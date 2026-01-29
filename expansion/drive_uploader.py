# expansion/drive_uploader.py

import os
import json
from typing import Dict

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# =====================================================
# CONFIG
# =====================================================
SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


# =====================================================
# DRIVE SERVICE
# =====================================================
def get_drive_service():
    """
    Crea cliente de Google Drive usando Service Account
    cargada desde la variable de entorno GOOGLE_SERVICE_ACCOUNT_JSON.
    Compatible con Shared Drives.
    """
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON no definido en variables de entorno"
        )

    try:
        info = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON no es JSON válido"
        ) from e

    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=SCOPES
    )

    return build(
        "drive",
        "v3",
        credentials=creds,
        cache_discovery=False  # 🔑 evita warnings y errores raros en prod
    )


# =====================================================
# UPLOAD
# =====================================================
def upload_file_to_drive(
    *,
    local_path: str,
    drive_folder_id: str,
    filename: str | None = None,
    mimetype: str = "text/csv"
) -> Dict[str, str]:
    """
    Sube un archivo a Google Drive (Shared Drive compatible).

    Retorna:
    {
        "file_id": str,
        "name": str,
        "webViewLink": str
    }
    """

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Archivo no encontrado: {local_path}")

    if not drive_folder_id:
        raise ValueError("drive_folder_id es obligatorio")

    service = get_drive_service()

    file_metadata = {
        "name": filename or os.path.basename(local_path),
        "parents": [drive_folder_id],
    }

    media = MediaFileUpload(
        local_path,
        mimetype=mimetype,
        resumable=True
    )

    try:
        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id,name,webViewLink",
                supportsAllDrives=True  # 🔑 CLAVE PARA SHARED DRIVES
            )
            .execute()
        )
    except Exception as e:
        raise RuntimeError(
            f"Error subiendo archivo a Google Drive: {e}"
        ) from e

    return {
        "file_id": file.get("id"),
        "name": file.get("name"),
        "webViewLink": file.get("webViewLink"),
    }
