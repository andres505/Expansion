import os
import sys
import subprocess


INEGI_LOCAL_DIR = "data/inegi/municipios"


def download_inegi_from_drive(folder_id: str):
    """
    Descarga los shapefiles de INEGI desde una carpeta de Google Drive
    SOLO si no existen localmente.
    """
    # Si la carpeta ya existe y tiene archivos, no volvemos a descargar.
    if os.path.exists(INEGI_LOCAL_DIR) and os.listdir(INEGI_LOCAL_DIR):
        print(f"[inegi_loader] Datos ya presentes en {INEGI_LOCAL_DIR}, se omite descarga.")
        return

    print(f"[inegi_loader] Descargando datos INEGI desde Drive (folder_id={folder_id})...")
    os.makedirs("data/inegi", exist_ok=True)

    subprocess.run(
        [
            sys.executable, "-m", "gdown",
            "--folder",
            f"https://drive.google.com/drive/folders/{folder_id}",
            "-O",
            INEGI_LOCAL_DIR,
            "--remaining-ok",
        ],
        check=True,
    )

    print(f"[inegi_loader] Descarga completada en {INEGI_LOCAL_DIR}.")
