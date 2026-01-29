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
    "types",                 # ARRAY
    "rating",
    "user_ratings_total",
    "price_level",
    "permanently_closed",
    "opening_hours",
    "raw_json",
]


def parse_types(value):
    if value is None or value == "":
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def to_string_safe(x):
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return json.dumps(x, ensure_ascii=False)
    if pd.isna(x):
        return None
    return str(x)


def places_csv_to_parquet(
    *,
    csv_path: str,
    parquet_path: str | None = None
) -> str:

    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    # folio → ID_lugar
    if "folio" in df.columns:
        df = df.rename(columns={"folio": "ID_lugar"})

    # asegurar columnas
    for col in BQ_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # viewport NO se infiere
    df["viewport"] = None

    # types → ARRAY
    df["types"] = df["types"].apply(parse_types)

    # todo lo demás → STRING
    for col in df.columns:
        if col != "types":
            df[col] = df[col].apply(to_string_safe)

    df = df[BQ_COLUMNS]

    if parquet_path is None:
        parquet_path = csv_path.replace(".csv", ".parquet")

    df.to_parquet(
        parquet_path,
        engine="pyarrow",
        index=False
    )

    return parquet_path
