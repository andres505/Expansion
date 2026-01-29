# expansion/places_to_parquet.py

import pandas as pd
import json
import os


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
    "viewport",
    "vicinity",
    "types",
    "rating",
    "user_ratings_total",
    "price_level",
    "permanently_closed",
    "opening_hours",
    "raw_json",
]


def places_csv_to_parquet(
    *,
    csv_path: str,
    parquet_path: str | None = None
) -> str:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)

    # -----------------------------
    # Renombres si aplica
    # -----------------------------
    if "folio" in df.columns:
        df = df.rename(columns={"folio": "ID_lugar"})

    # -----------------------------
    # Asegurar columnas
    # -----------------------------
    for col in BQ_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[BQ_COLUMNS]

    # -----------------------------
    # Forzar STRING en todo
    # -----------------------------
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: json.dumps(x, ensure_ascii=False)
            if isinstance(x, (dict, list))
            else None if pd.isna(x) else str(x)
        )

    if parquet_path is None:
        parquet_path = csv_path.replace(".csv", ".parquet")

    df.to_parquet(
        parquet_path,
        engine="pyarrow",
        index=False
    )

    return parquet_path
