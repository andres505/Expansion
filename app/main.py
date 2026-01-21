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


@app.post("/run-expansion")
def run_expansion(payload: ExpansionRequest):
    return {
        "status": "received",
        "payload": payload
    }
