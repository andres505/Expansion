from fastapi import FastAPI

app = FastAPI(title="Expansion NETO API")

@app.get("/health")
def health():
    return {"ok": True}
from pydantic import BaseModel

class ExpansionRequest(BaseModel):
    id_ubicacion: str
    latitud: float
    longitud: float
    telefono: str | None = None
    id_carpeta_drive: str | None = None
    tipo_sitio: str | None = None
    tipo_adquisicion: str | None = None
    ubicacion_en_manzana: str | None = None


from expansion.geo import load_neto_master, get_nearest_neto_store
from expansion.payload_builder import build_payload_flat

@app.post("/run-expansion")
def run_expansion(payload: ExpansionRequest):

    # 1. JSON → dict plano
    input_data = payload.model_dump()

    # 2. Cargar master NETO
    df_neto = load_neto_master()

    # 3. Calcular tienda NETO más cercana
    nearest_store = get_nearest_neto_store(
        lat=input_data["latitud"],
        lon=input_data["longitud"],
        df_neto=df_neto
    )

    # 4. Construir payload base del pipeline
    payload_flat = build_payload_flat(
        input_data=input_data,
        nearest_store=nearest_store
    )

    return {
        "status": "base_pipeline_ok",
        "payload_flat": payload_flat
    }
