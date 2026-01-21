from fastapi import FastAPI
from pydantic import BaseModel
import os

# =========================
# APP
# =========================
app = FastAPI(title="Expansion NETO API")


# =========================
# MODELO DE ENTRADA
# =========================
class ExpansionRequest(BaseModel):
    id_ubicacion: str
    latitud: float
    longitud: float
    telefono: str | None = None
    id_carpeta_drive: str | None = None
    tipo_sitio: str | None = None
    tipo_adquisicion: str | None = None
    ubicacion_en_manzana: str | None = None


# =========================
# IMPORTS PIPELINE
# =========================
from expansion.geo import load_neto_master, get_nearest_neto_store
from expansion.inegi import load_inegi_gdf, find_municipio_inegi
from expansion.payload_builder import build_payload_flat
from expansion.inegi_loader import download_inegi_from_drive


# =========================
# GLOBALS (CARGA ÚNICA)
# =========================
DF_NETO = None
GDF_INEGI = None


# =========================
# STARTUP (SE EJECUTA 1 VEZ)
# =========================
@app.on_event("startup")
def startup():

    global DF_NETO, GDF_INEGI

    # --- NETO MASTER ---
    DF_NETO = load_neto_master(
        excel_path="data/MASTER_FINAL_TIENDAS.xlsx"
    )

    # --- INEGI ---
    folder_id = os.environ.get("INEGI_DRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("INEGI_DRIVE_FOLDER_ID not set")

    download_inegi_from_drive(folder_id)

    GDF_INEGI = load_inegi_gdf(
        "data/inegi/municipios/00mun.shp"
    )


# =========================
# HEALTH
# =========================
@app.get("/health")
def health():
    return {"ok": True}


# =========================
# ENDPOINT PRINCIPAL
# =========================
@app.post("/run-expansion")
def run_expansion(payload: ExpansionRequest):

    # 1. JSON → dict
    input_data = payload.model_dump()

    lat = input_data["latitud"]
    lon = input_data["longitud"]

    # 2. Tienda NETO más cercana
    nearest_store = get_nearest_neto_store(
        lat=lat,
        lon=lon,
        df_stores=DF_NETO
    )

    # 3. INEGI
    inegi_raw = find_municipio_inegi(
        lat=lat,
        lon=lon,
        gdf_inegi=GDF_INEGI
    )

    inegi_data = {
        f"INEGI_{k}": v
        for k, v in inegi_raw.items()
    }

    # 4. Payload plano base
    payload_flat = build_payload_flat(
        lat=lat,
        lon=lon,
        neto_data=nearest_store,
        inegi_data=inegi_data,
        places_count={},        # siguiente paso
        competencia_data={}     # siguiente paso
    )

    return {
        "status": "base_pipeline_ok",
        "payload_flat": payload_flat
    }
