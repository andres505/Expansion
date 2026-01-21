import time
import json
import os
from collections import defaultdict
from datetime import datetime

import googlemaps
import pandas as pd


# ======================================================
# POI TYPES (definidos por negocio)
# ======================================================
POI_TYPES = [
    "supermarket", "convenience_store", "shopping_mall", "department_store",
    "store", "bus_station", "subway_station", "train_station", "transit_station",
    "primary_school", "secondary_school", "university",
    "hospital", "pharmacy", "drugstore",
    "atm", "bank",
    "bakery", "restaurant", "cafe", "bar",
    "hardware_store", "home_goods_store",
    "gas_station", "car_repair", "car_wash", "laundry",
    "church", "city_hall", "local_government_office",
    "courthouse", "police", "fire_station",
    "park", "stadium", "cemetery"
]

# ======================================================
# GOOGLE MAPS CLIENT (HARDCODE TEMPORAL)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================
def fetch_places_nearby(
    *,
    folio: str,
    lat: float,
    lon: float,
    radius_m: int = 500,
    sleep_s: float = 1.0,
    output_dir: str = "outputs/google_places",
):
    """
    Consulta Google Places Nearby.

    Retorna:
    - df_places (DataFrame)
    - conteo_por_tipo (dict)
    - csv_path (str)
    """

    os.makedirs(output_dir, exist_ok=True)

    all_rows = []
    conteo = defaultdict(int)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    lat_str = f"{lat:.6f}".replace(".", "_")
    lon_str = f"{lon:.6f}".replace(".", "_")

    csv_name = (
        f"google_places_folio_{folio}_"
        f"lat_{lat_str}_lon_{lon_str}_{timestamp}.csv"
    )
    csv_path = os.path.join(output_dir, csv_name)

    for poi_type in POI_TYPES:
        response = gmaps.places_nearby(
            location=(lat, lon),
            radius=radius_m,
            type=poi_type
        )

        while True:
            results = response.get("results", [])
            conteo[poi_type] += len(results)

            for r in results:
                all_rows.append({
                    "folio": folio,
                    "query_lat": lat,
                    "query_lon": lon,
                    "search_radius_m": radius_m,
                    "poi_type_searched": poi_type,

                    "place_id": r.get("place_id"),
                    "name": r.get("name"),
                    "business_status": r.get("business_status"),

                    "place_lat": r.get("geometry", {}).get("location", {}).get("lat"),
                    "place_lon": r.get("geometry", {}).get("location", {}).get("lng"),

                    "vicinity": r.get("vicinity"),
                    "types": json.dumps(r.get("types"), ensure_ascii=False),

                    "rating": r.get("rating"),
                    "user_ratings_total": r.get("user_ratings_total"),
                    "price_level": r.get("price_level"),

                    "opening_hours": json.dumps(
                        r.get("opening_hours"), ensure_ascii=False
                    ),

                    "raw_json": json.dumps(r, ensure_ascii=False)
                })

            if "next_page_token" in response:
                time.sleep(2)
                response = gmaps.places_nearby(
                    page_token=response["next_page_token"]
                )
            else:
                break

        time.sleep(sleep_s)

    df_places = pd.DataFrame(all_rows)
    df_places.to_csv(csv_path, index=False, encoding="utf-8-sig")

    conteo["total_lugares"] = int(sum(conteo.values()))

    return df_places, dict(conteo), csv_path
