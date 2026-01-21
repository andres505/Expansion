import pandas as pd
import numpy as np
import re
from typing import Dict, List


# =====================================================
# UTILIDADES
# =====================================================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    return 2 * R * np.arcsin(np.sqrt(a))


def normalize_chain(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.upper().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def classify_chain(name: str) -> str:
    """
    Clasificación ejecutiva de competencia.
    """
    n = normalize_chain(name)

    if "AURRERA" in n:
        return "BODEGA_AURRERA"
    if "3B" in n:
        return "TIENDAS_3B"
    if "NETO" in n:
        return "NETO"

    return "OTRAS"


# =====================================================
# FUNCIÓN PRINCIPAL
# =====================================================
def get_competencia_por_radio(
    *,
    lat: float,
    lon: float,
    df_generales: pd.DataFrame,
    df_aurrera: pd.DataFrame,
    radio_m: int = 500
) -> Dict:

    radio_km = radio_m / 1000.0
    rows: List[Dict] = []

    # -----------------------------
    # TIENDAS GENERALES
    # -----------------------------
    df_gen = df_generales.copy()

    df_gen["lat"] = pd.to_numeric(df_gen["LAT"], errors="coerce")
    df_gen["lon"] = pd.to_numeric(df_gen["LONG"], errors="coerce")

    df_gen["CADENA_NORM"] = df_gen["CADENA"].apply(normalize_chain)

    df_gen["dist_km"] = haversine_km(
        lat, lon,
        df_gen["lat"].values,
        df_gen["lon"].values
    )

    df_gen = df_gen[df_gen["dist_km"] <= radio_km]

    # Deduplicación por tienda física
    df_gen["lat_round"] = df_gen["lat"].round(4)
    df_gen["lon_round"] = df_gen["lon"].round(4)

    df_gen = df_gen.drop_duplicates(
        subset=["CADENA_NORM", "lat_round", "lon_round"]
    )

    for _, r in df_gen.iterrows():
        cat = classify_chain(r["CADENA_NORM"])
        if cat == "NETO":
            continue

        rows.append({
            "categoria": cat,
            "nombre": r["CADENA_NORM"],
            "dist_km": round(float(r["dist_km"]), 3)
        })

    # -----------------------------
    # BODEGA AURRERA (BASE PROPIA)
    # -----------------------------
    df_au = df_aurrera.copy()

    df_au["lat"] = pd.to_numeric(df_au["latitud"], errors="coerce")
    df_au["lon"] = pd.to_numeric(df_au["longitud"], errors="coerce")

    df_au["NOMBRE_NORM"] = df_au["nombre"].apply(normalize_chain)

    df_au["dist_km"] = haversine_km(
        lat, lon,
        df_au["lat"].values,
        df_au["lon"].values
    )

    df_au = df_au[df_au["dist_km"] <= radio_km]

    df_au["lat_round"] = df_au["lat"].round(4)
    df_au["lon_round"] = df_au["lon"].round(4)

    df_au = df_au.drop_duplicates(
        subset=["NOMBRE_NORM", "lat_round", "lon_round"]
    )

    for _, r in df_au.iterrows():
        rows.append({
            "categoria": "BODEGA_AURRERA",
            "nombre": r["NOMBRE_NORM"],
            "dist_km": round(float(r["dist_km"]), 3)
        })

    # =====================================================
    # ARMADO FINAL
    # =====================================================
    out = {
        "bodega_aurrera": [],
        "tiendas_3b": [],
        "otras_competencias": []
    }

    for r in rows:
        if r["categoria"] == "BODEGA_AURRERA":
            out["bodega_aurrera"].append(r)
        elif r["categoria"] == "TIENDAS_3B":
            out["tiendas_3b"].append(r)
        else:
            out["otras_competencias"].append(r)

    resumen = {
        "total": len(rows),
        "bodega_aurrera": len(out["bodega_aurrera"]),
        "tiendas_3b": len(out["tiendas_3b"]),
        "otras": len(out["otras_competencias"])
    }

    out["competencia_resumen"] = resumen

    return out
