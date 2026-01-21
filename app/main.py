from fastapi import FastAPI
from pydantic import BaseModel
import os
import pandas as pd

# =====================================================
# APP
# =====================================================
app = FastAPI(title="Expansion NETO API")


# =====================================================
# MODELO DE ENTRADA
# =====================================================
class ExpansionRequest(BaseModel):
    id_ubicacion: str
    latitud: float
    longitud: float
    telefono: str | None = None
    id_carpeta_drive: str | None = None
    tipo_sitio: str | None = None
    tipo_adquisicion: str | None = None
    ubicacion_en_manzana: str | None = None


# =====================================================
# IMPORTS PIPELINE
# =====================================================
from expansion.geo import load_neto_master, get_nearest_neto_store
from expansion.inegi import find_municipio_inegi, prefix_inegi_keys
from expansion.payload_builder import build_payload_flat
from expansion.inegi_loader import download_inegi_from_drive
import geopandas as gpd


# =====================================================
# GLOBALS (SE CARGAN UNA VEZ)
# =====================================================
DF_NETO = None
GDF_INEGI = None
DF_INEGI_TABULAR = None


# =====================================================
# STARTUP
# =====================================================
@app.on_event("startup")
def startup():
    global DF_NETO, GDF_INEGI, DF_INEGI_TABULAR

    # ---------------------------
    # NETO MASTER
    # ---------------------------
    DF_NETO = load_neto_master(
        excel_path="data/MASTER_FINAL_TIENDAS.xlsx"
    )

    # ---------------------------
    # INEGI GEO (Shapefile)
    # ---------------------------
    folder_id = os.environ.get("INEGI_DRIVE_FOLDER_ID")

    inegi_shp = "data/inegi/municipios/00mun.shp"

    if folder_id and not os.path.exists(inegi_shp):
        download_inegi_from_drive(folder_id)

    if os.path.exists(inegi_shp):
        GDF_INEGI = gpd.read_file(inegi_shp)
        if GDF_INEGI.crs is None:
            GDF_INEGI = GDF_INEGI.set_crs(epsg=4326)
    else:
        GDF_INEGI = None

    # ---------------------------
    # INEGI TABULAR (CSV hogares)
    # ---------------------------
    try:
        DF_INEGI_TABULAR = pd.read_csv(
            "data/data_hogares.csv",
            dtype=str
        )

        # Normalización INEGI
        DF_INEGI_TABULAR["CVE_ENT"] = DF_INEGI_TABULAR["CVE_ENT"].str.zfill(2)
        DF_INEGI_TABULAR["CVE_MUN"] = DF_INEGI_TABULAR["CVE_MUN"].str.zfill(3)

        DF_INEGI_TABULAR["CVEGEO"] = (
            DF_INEGI_TABULAR["CVE_ENT"]
            + DF_INEGI_TABULAR["CVE_MUN"]
        )

    except Exception:
        DF_INEGI_TABULAR = None


# =====================================================
# HEALTH
# =====================================================
@app.get("/health")
def health():
    return {"ok": True}


# =====================================================
# ENDPOINT PRINCIPAL
# =====================================================
@app.post("/run-expansion")
def run_expansion(payload: ExpansionRequest):

    # ---------------------------
    # INPUT
    # ---------------------------
    input_data = payload.model_dump()
    lat = input_data["latitud"]
    lon = input_data["longitud"]

    # ---------------------------
    # NETO MÁS CERCANA
    # ---------------------------
    nearest_store = get_nearest_neto_store(
        lat=lat,
        lon=lon,
        df_stores=DF_NETO
    )

    # ---------------------------
    # INEGI GEO
    # ---------------------------
    inegi_geo_raw = {}
    if GDF_INEGI is not None:
        inegi_geo_raw = find_municipio_inegi(
            lat=lat,
            lon=lon,
            gdf_inegi=GDF_INEGI
        )

    # ---------------------------
    # INEGI TABULAR (por CVEGEO)
    # ---------------------------
    inegi_tab_raw = {}
    cvegeo = inegi_geo_raw.get("CVEGEO")

    if cvegeo and DF_INEGI_TABULAR is not None:
        row = DF_INEGI_TABULAR.loc[
            DF_INEGI_TABULAR["CVEGEO"] == str(cvegeo)
        ]
        if not row.empty:
            inegi_tab_raw = row.iloc[0].to_dict()

    # ---------------------------
    # MERGE + PREFIJO INEGI_
    # ---------------------------
    inegi_data = prefix_inegi_keys({
        **inegi_geo_raw,
        **inegi_tab_raw
    })

    # ---------------------------
    # PAYLOAD FINAL BASE
    # ---------------------------
    payload_flat = build_payload_flat(
        lat=lat,
        lon=lon,
        neto_data=nearest_store,
        inegi_data=inegi_data,
        places_count={},        # siguiente módulo
        competencia_data={}     # siguiente módulo
    )

    return {
        "status": "base_pipeline_ok",
        "payload_flat": payload_flat
    }
