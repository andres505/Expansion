# expansion/integracion_comercial.py

import numpy as np
import pandas as pd
from typing import Dict, Any


# =====================================================
# CONFIGURACIÓN BASELINE (METRO SUR)
# =====================================================

RADIOS_CLAVE = [20, 50, 100, 150, 200, 300, 400, 500]

UMBRALES_METRO_SUR = {
    20:  {"rojo": 1,   "amarillo": 4},
    50:  {"rojo": 4,   "amarillo": 9},
    100: {"rojo": 14,  "amarillo": 29},
    150: {"rojo": 29,  "amarillo": 59},
    200: {"rojo": 49,  "amarillo": 79},
    300: {"rojo": 99,  "amarillo": 149},
    400: {"rojo": 149, "amarillo": 189},
    500: {"rojo": 199, "amarillo": 249},
}

PESOS = {
    20: 5,
    50: 5,
    100: 25,
    150: 10,
    200: 25,
    300: 15,
    400: 10,
    500: 5,
}


# =====================================================
# UTILIDAD: DISTANCIA HAVERSINE (m)
# =====================================================
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    return 2 * R * np.arcsin(np.sqrt(a))


# =====================================================
# FUNCIÓN PRINCIPAL
# =====================================================
def evaluar_integracion_comercial_desde_csv(
    csv_path: str
) -> Dict[str, Any]:
    """
    Evalúa la integración comercial de un sitio usando
    el CSV crudo de Google Places.

    Retorna un dict PLANO listo para:
    - payload
    - prompt LLM
    - BigQuery
    """

    # -----------------------------
    # Cargar CSV
    # -----------------------------
    df = pd.read_csv(
        csv_path,
        encoding="latin1",
        engine="python",
        sep=",",
        on_bad_lines="skip"
    )

    df.columns = (
        df.columns
        .str.replace("ï»¿", "", regex=False)
        .str.strip()
    )

    for c in ["query_lat", "query_lon", "place_lat", "place_lon"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["query_lat", "query_lon", "place_lat", "place_lon"])

    if df.empty:
        return {
            "integracion_score": 0,
            "integracion_clasificacion": "SIN_DATOS",
            "integracion_diagnostico": "No se encontraron lugares válidos en el CSV."
        }

    # -----------------------------
    # Calcular distancia
    # -----------------------------
    df["distance_m"] = haversine_m(
        df["query_lat"],
        df["query_lon"],
        df["place_lat"],
        df["place_lon"]
    )

    # -----------------------------
    # Conteos por radio
    # -----------------------------
    conteos = {
        r: int((df["distance_m"] <= r).sum())
        for r in RADIOS_CLAVE
    }

    # -----------------------------
    # Evaluación por radio
    # -----------------------------
    detalle = {}
    score_total = 0.0

    for r in RADIOS_CLAVE:
        val = conteos[r]
        umb = UMBRALES_METRO_SUR[r]

        if val <= umb["rojo"]:
            semaforo = "ROJO"
            subscore = 0.0
        elif val <= umb["amarillo"]:
            semaforo = "AMARILLO"
            subscore = 0.5
        else:
            semaforo = "VERDE"
            subscore = 1.0

        aporte = subscore * PESOS[r]
        score_total += aporte

        detalle[r] = {
            "generadores": val,
            "semaforo": semaforo,
            "peso": PESOS[r],
            "aporte_score": round(aporte, 2)
        }

    score_total = round(score_total, 1)

    # -----------------------------
    # Clasificación final
    # -----------------------------
    if score_total >= 70:
        clasificacion = "INTEGRADO"
    elif score_total >= 50:
        clasificacion = "PERIFERICO"
    else:
        clasificacion = "AISLADO"

    # -----------------------------
    # Diagnóstico ejecutivo
    # -----------------------------
    if detalle[100]["semaforo"] == "ROJO" and detalle[200]["semaforo"] == "ROJO":
        diagnostico = (
            "El sitio presenta aislamiento comercial temprano hasta 200 m; "
            "la actividad comercial se concentra a distancias mayores."
        )
    elif detalle[100]["semaforo"] == "VERDE" or detalle[200]["semaforo"] == "VERDE":
        diagnostico = (
            "El sitio muestra integración comercial temprana "
            "dentro del entorno inmediato."
        )
    else:
        diagnostico = (
            "El sitio presenta integración comercial parcial; "
            "la zona comercial existe, pero no envuelve completamente al punto."
        )

    # -----------------------------
    # SALIDA PLANA
    # -----------------------------
    output = {
        "integracion_score": score_total,
        "integracion_clasificacion": clasificacion,
        "integracion_diagnostico": diagnostico,
    }

    for r in RADIOS_CLAVE:
        output[f"integracion_{r}m"] = conteos[r]

    return output
