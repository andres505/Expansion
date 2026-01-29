# expansion/places_to_parquet.py

import pandas as pd
import json
import os


# ======================================================
# COLUMNAS EXACTAS DE BIGQUERY (orden importa)
# ======================================================
BQ_COLUMNS = [
    "ID_lugar",
    "query_lat",
    "query_lon",
    "search_radius_m",
    "poi_type_searched",
    "place_id",
    "name",
    "business_status",
    "place_lat",
    "place_lon",
    "viewport",              # STRING en BQ (se fuerza a NULL)
    "vicinity",
    "types",
    "rating",
    "user_ratings_total",
    "price_level",
    "permanently_closed",
    "opening_hours",
    "raw_json",
]


# ======================================================
# HELPERS
# ======================================================
def _to_string_safe(x):
    """
    Convierte cualquier valor a STRING compatible con BigQuery.
    - dict / list -> JSON string
    - NaN / None -> None
    - resto -> str
    """
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return json.dumps(x, ensure_ascii=False)
    if pd.isna(x):
        return None
    return str(x)


# ======================================================
# MAIN
# ======================================================
def places_csv_to_parquet(
    *,
    csv_path: str,
    parquet_path: str | None = None
) -> str:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)

    # --------------------------------------------------
    # Leer CSV
    # --------------------------------------------------
    df = pd.read_csv(csv_path)

    # --------------------------------------------------
    # Renombres
    # --------------------------------------------------
    if "folio" in df.columns:
        df = df.rename(columns={"folio": "ID_lugar"})

    # --------------------------------------------------
    # Asegurar TODAS las columnas del schema BQ
    # --------------------------------------------------
    for col in BQ_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # --------------------------------------------------
    # 🔴 FIX CRÍTICO
    # viewport NO viene del CSV
    # y NO debe inferirse → siempre STRING NULL
    # --------------------------------------------------
    df["viewport"] = None

    # --------------------------------------------------
    # Reordenar exactamente como BQ
    # --------------------------------------------------
    df = df[BQ_COLUMNS]

    # --------------------------------------------------
    # Forzar STRING en TODO
    # --------------------------------------------------
    for col in df.columns:
        df[col] = df[col].apply(_to_string_safe).astype("string")

    # --------------------------------------------------
    # Output parquet
    # --------------------------------------------------
    if parquet_path is None:
        parquet_path = csv_path.replace(".csv", ".parquet")

    df.to_parquet(
        parquet_path,
        engine="pyarrow",
        index=False
    )

    return parquet_path
