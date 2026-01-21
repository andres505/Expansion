import os
import subprocess

INEGI_LOCAL_DIR = "data/inegi/municipios"


def download_inegi_from_drive(folder_id: str):
    """
    Descarga los shapefiles de INEGI desde una carpeta de Google Drive
    SOLO si no existen localmente.
    """

    if os.path.exists(INEGI_LOCAL_DIR):
        # Ya está descargado
        return

    os.makedirs("data/inegi", exist_ok=True)

    subprocess.run(
        [
            "gdown",
            "--folder",
            f"https://drive.google.com/drive/folders/{folder_id}",
            "-O",
            INEGI_LOCAL_DIR,
            "--remaining-ok"
        ],
        check=True
    )
