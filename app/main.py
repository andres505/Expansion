from fastapi import FastAPI

app = FastAPI(title="Expansion NETO API")

@app.get("/health")
def health():
    return {"ok": True}
