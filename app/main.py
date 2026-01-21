from fastapi import FastAPI
from pydantic import BaseModel
import os
import pandas as pd

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
from expansion.inegi import (
    load_inegi_gdf,
    find_municipio_inegi,
    prefix_inegi_keys
)
from expansion.payload_builder import build_payload_flat
from expansion.inegi_loader import download_inegi_from_drive


# =========================
# GLOBALS (CARGA ÚNICA)
# =========================
DF_NETO = None
GDF_INEGI = None
DF_INEGI_TABULAR = None


# =========================
# STARTUP (SE EJECUTA 1 VEZ)
# =========================
@app.on_event("startup")
def startup():

    global DF_NETO, GDF_INEGI, DF_INEGI_TABULAR

    # --- NETO MASTER ---
    DF_NETO = load_neto_master(
        excel_path="data/MASTER_FINAL_TIENDAS.xlsx"
    )

    # --- INEGI GEO (Drive) ---
    folder_id = os.environ.get("INEGI_DRIVE_FOLDER_ID")
    if folder_id:
        download_inegi_from_drive(folder_id)

        inegi_shp = "data/inegi/municipios/00mun.shp"
        if os.path.exists(inegi_shp):
            GDF_INEGI = load_inegi_gdf(inegi_shp)
        else:
            GDF_INEGI = None
    else:
        GDF_INEGI = None

    # --- INEGI TABULAR (CSV hogares) ---
    try:
        DF_INEGI_TABULAR = pd.read_csv(
            "data/data_hogares.csv",
            dtype={"CVEGEO": str}
        )
    except Exception:
        DF_INEGI_TABULAR = None


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

    # 3. INEGI GEO
    if GDF_INEGI is not None:
        inegi_geo_raw = find_municipio_inegi(
            lat=lat,
            lon=lon,
            gdf_inegi=GDF_INEGI
        )
    else:
        inegi_geo_raw = {}

    # 4. INEGI TABULAR (CSV por CVEGEO)
    inegi_tab_raw = {}
    cvegeo = inegi_geo_raw.get("CVEGEO")

    if cvegeo and DF_INEGI_TABULAR is not None:
        row = DF_INEGI_TABULAR.loc[
            DF_INEGI_TABULAR["CVEGEO"] == str(cvegeo)
        ]
        if not row.empty:
            inegi_tab_raw = row.iloc[0].to_dict()

    # 5. Merge + prefijo INEGI_*
    inegi_data = prefix_inegi_keys({
        **inegi_geo_raw,
        **inegi_tab_raw
    })

    # 6. Payload plano base
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
