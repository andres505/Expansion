import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from typing import Dict


# =====================================================
# CONFIGURACIÓN
# =====================================================
RELEVANT_COLUMNS = [
    "STORE_ID",
    "FCTIENDA",
    "FCREGION",
    "FCZONA",
    "FCESTADO",
    "FCLATITUD",
    "FCLONGITUD",
    "Existencia Costo",
    "Existencia Piezas",
    "Venta Sin Impuestos",
    "Venta Costo",
    "Venta Piezas",
    "Transacciones",
    "Ticket Promedio",
    "Prom Cantidad",
    "Prom Monto Sin Imp"
]


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


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


# =====================================================
# CARGA MASTER NETO
# =====================================================
def load_neto_master(
    excel_path: str = "data/MASTER_FINAL_TIENDAS.xlsx"
) -> pd.DataFrame:

    """
    Carga y normaliza el master de tiendas NETO.
    """
    df = pd.read_excel(excel_path)
    df = df[RELEVANT_COLUMNS].copy()

    df["FCLATITUD"] = pd.to_numeric(df["FCLATITUD"], errors="coerce")
    df["FCLONGITUD"] = pd.to_numeric(df["FCLONGITUD"], errors="coerce")

    numeric_cols = [
        "Existencia Costo",
        "Existencia Piezas",
        "Venta Sin Impuestos",
        "Venta Costo",
        "Venta Piezas",
        "Transacciones",
        "Prom Cantidad",
        "Ticket Promedio",
        "Prom Monto Sin Imp"
    ]

    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["FCLATITUD", "FCLONGITUD"])

    return df


# =====================================================
# TIENDA NETO MÁS CERCANA
# =====================================================
def get_nearest_neto_store(
    lat: float,
    lon: float,
    df_stores: pd.DataFrame
) -> Dict:
    """
    Encuentra la tienda NETO más cercana y devuelve
    métricas clave para expansión.
    """
    df = df_stores.copy()

    df["dist_km"] = haversine_km(
        lat, lon,
        df["FCLATITUD"].values,
        df["FCLONGITUD"].values
    )

    nearest = df.loc[df["dist_km"].idxmin()]

    return {
        "lat": lat,
        "longitud": lon,
        "estado": nearest["FCESTADO"],
        "region": nearest["FCREGION"],

        "id_tienda_cercana": int(nearest["STORE_ID"]),
        "distancia_tienda_cercana_km": round(float(nearest["dist_km"]), 4),

        "tienda_cercanaExistencia_Costo": _safe_float(nearest["Existencia Costo"]),
        "tienda_cercanaExistencia_Piezas": _safe_float(nearest["Existencia Piezas"]),
        "tienda_cercanaVenta_Sin_Impuestos": _safe_float(nearest["Venta Sin Impuestos"]),
        "tienda_cercanaVenta_Costo": _safe_float(nearest["Venta Costo"]),
        "tienda_cercanaVenta_Piezas": _safe_float(nearest["Venta Piezas"]),
        "tienda_cercanaTransacciones": _safe_float(nearest["Transacciones"]),
        "tienda_cercanaTicket_Promedio": _safe_float(nearest["Ticket Promedio"]),
        "tienda_cercanaProm_Cantidad": _safe_float(nearest["Prom Cantidad"]),
        "tienda_cercanaProm_Monto_Sin_Imp": _safe_float(nearest["Prom Monto Sin Imp"]),
    }


# =====================================================
# INEGI – MUNICIPIO
# =====================================================
def find_municipio_inegi(
    lat: float,
    lon: float,
    gdf_inegi: gpd.GeoDataFrame
) -> Dict:
    """
    Devuelve el municipio INEGI que contiene el punto.
    Incluye fallback por borde / nearest.
    """
    pt = gpd.GeoDataFrame(
        geometry=[Point(lon, lat)],
        crs="EPSG:4326"
    )

    hit = gpd.sjoin(pt, gdf_inegi, how="left", predicate="within")

    if not hit.empty and not hit.iloc[0].isna().all():
        return hit.iloc[0].drop("geometry").to_dict()

    # Fallback buffer
    pt_m = pt.to_crs(epsg=6372)
    pt_m["geometry"] = pt_m.geometry.buffer(5)
    pt_b = pt_m.to_crs(epsg=4326)

    hit = gpd.sjoin(pt_b, gdf_inegi, how="left", predicate="intersects")
    if not hit.empty and not hit.iloc[0].isna().all():
        return hit.iloc[0].drop("geometry").to_dict()

    # Último fallback: nearest
    pt_m = pt.to_crs(epsg=6372)
    gdf_m = gdf_inegi.to_crs(epsg=6372)

    near = gpd.sjoin_nearest(pt_m, gdf_m, how="left", max_distance=300)
    if not near.empty:
        return gdf_inegi.iloc[near["index_right"].iloc[0]].drop("geometry").to_dict()

    return {
        "INEGI_FOUND": False
    }
