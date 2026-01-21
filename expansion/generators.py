import json
import pandas as pd
import numpy as np

# ======================================================
# MAPEO DE GENERADORES
# ======================================================
GENERATOR_CATEGORIES = {
    "educacion": [
        "primary_school", "secondary_school", "school", "university"
    ],
    "salud": [
        "hospital", "pharmacy", "drugstore"
    ],
    "transporte": [
        "bus_station", "subway_station", "train_station", "transit_station"
    ],
    "gobierno": [
        "city_hall", "courthouse", "police", "fire_station"
    ],
    "consumo": [
        "supermarket", "convenience_store", "shopping_mall", "department_store"
    ],
    "alimentos": [
        "restaurant", "cafe", "bakery"
    ],
    "recreacion": [
        "park", "stadium"
    ]
}


# ======================================================
# UTILIDAD: distancia haversine
# ======================================================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    return 2 * R * np.arcsin(np.sqrt(a))


# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================
def build_generators_summary(
    *,
    df_places: pd.DataFrame,
    lat: float,
    lon: float
):
    """
    Clasifica y resume generadores de tráfico a partir
    de Google Places crudo.

    Retorna:
    - resumen_generadores (dict)
    - tabla_generadores (DataFrame)
    """

    if df_places.empty:
        return {}, pd.DataFrame()

    df = df_places.copy()

    # --------------------------------------------------
    # Parsear types
    # --------------------------------------------------
    df["types_list"] = df["types"].apply(
        lambda x: json.loads(x) if isinstance(x, str) else []
    )

    # --------------------------------------------------
    # Calcular distancia
    # --------------------------------------------------
    df["dist_km"] = haversine_km(
        lat,
        lon,
        df["place_lat"].values,
        df["place_lon"].values
    )

    rows = []

    # --------------------------------------------------
    # Clasificación por categoría
    # --------------------------------------------------
    for categoria, google_types in GENERATOR_CATEGORIES.items():
        mask = df["types_list"].apply(
            lambda lst: any(t in lst for t in google_types)
        )

        df_cat = df[mask].copy()

        if df_cat.empty:
            continue

        rows.append({
            "categoria": categoria,
            "total_lugares": int(len(df_cat)),
            "distancia_min_km": float(df_cat["dist_km"].min()),
            "distancia_prom_km": float(df_cat["dist_km"].mean())
        })

    tabla_generadores = pd.DataFrame(rows)

    # --------------------------------------------------
    # Resumen ejecutivo (dict)
    # --------------------------------------------------
    resumen_generadores = {
        "generadores_total": int(tabla_generadores["total_lugares"].sum())
        if not tabla_generadores.empty else 0
    }

    for _, r in tabla_generadores.iterrows():
        resumen_generadores[f"generadores_{r['categoria']}_count"] = int(r["total_lugares"])
        resumen_generadores[f"generadores_{r['categoria']}_min_dist_km"] = round(
            r["distancia_min_km"], 3
        )

    return resumen_generadores, tabla_generadores
