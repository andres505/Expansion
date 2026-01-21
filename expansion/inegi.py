import geopandas as gpd
from shapely.geometry import Point
from typing import Dict


# =====================================================
# LOAD INEGI GEO DATA
# =====================================================
def load_inegi_gdf(shp_path: str) -> gpd.GeoDataFrame:
    """
    Carga el shapefile de municipios INEGI y normaliza CRS.
    """
    gdf = gpd.read_file(shp_path)

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    return gdf


# =====================================================
# FIND MUNICIPIO INEGI
# =====================================================
def find_municipio_inegi(
    lat: float,
    lon: float,
    gdf_inegi: gpd.GeoDataFrame
) -> Dict:
    """
    Devuelve el municipio INEGI que contiene el punto.
    Incluye fallback por buffer y nearest.
    """

    pt = gpd.GeoDataFrame(
        geometry=[Point(lon, lat)],
        crs="EPSG:4326"
    )

    # 1. Within
    hit = gpd.sjoin(pt, gdf_inegi, how="left", predicate="within")
    if not hit.empty and not hit.iloc[0].isna().all():
        return hit.iloc[0].drop("geometry").to_dict()

    # 2. Buffer pequeño (~5m)
    pt_m = pt.to_crs(epsg=6372)
    pt_m["geometry"] = pt_m.geometry.buffer(5)
    pt_b = pt_m.to_crs(epsg=4326)

    hit = gpd.sjoin(pt_b, gdf_inegi, how="left", predicate="intersects")
    if not hit.empty and not hit.iloc[0].isna().all():
        return hit.iloc[0].drop("geometry").to_dict()

    # 3. Nearest (hasta 300m)
    pt_m = pt.to_crs(epsg=6372)
    gdf_m = gdf_inegi.to_crs(epsg=6372)

    near = gpd.sjoin_nearest(pt_m, gdf_m, how="left", max_distance=300)
    if not near.empty:
        return gdf_inegi.iloc[
            near["index_right"].iloc[0]
        ].drop("geometry").to_dict()

    return {"INEGI_FOUND": False}


# =====================================================
# PREFIX KEYS (TU FUNCIÓN ORIGINAL)
# =====================================================
def prefix_inegi_keys(inegi_data: dict) -> dict:
    """
    Prefija todas las llaves INEGI con 'INEGI_'.
    Asume input plano (sin prefijo).
    """
    if not inegi_data:
        return {}

    out = {}
    for k, v in inegi_data.items():
        if k.startswith("INEGI_"):
            out[k] = v
        else:
            out[f"INEGI_{k}"] = v
    return out
