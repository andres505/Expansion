import json

def normalize_region_name(region: str) -> str:
    return (
        region.strip()
              .upper()
              .replace("Á", "A")
              .replace("É", "E")
              .replace("Í", "I")
              .replace("Ó", "O")
              .replace("Ú", "U")
              .replace("Ü", "U")
              .replace("Ñ", "N")
    )


REGION_ALIAS = {
    "OAXACA COSTA": "OAXACA",

    # Taxonomía nueva del master de tiendas (refresh Jul25-Jun26) que aún no
    # existe en vectores_promedio_region.json. Mapeo a la región vieja más
    # cercana geográficamente (mayoría de tiendas de la región nueva) hasta
    # regenerar los vectores con la taxonomía nueva.
    "ACAPULCO CENTRO": "ACA ORIENTE",
    "CHIAPAS SOCONUSCO": "CHIAPAS",
    "COATZA OLMECA": "TABASCO",
    "IZTAPALAPA": "NEZA",
    "OAXACA MIXTECA": "OAXACA",
    "OCCIDENTE BAJIO": "BAJIO",
    "OCCIDENTE MICHOACAN NORTE": "MICHOACAN",
    "OCCIDENTE MICHOACAN SUR": "MICHOACAN",
    "VALLE": "NEZA",
}


def load_region_vector_for_prompt(json_path: str, region: str) -> dict:

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    region_norm = normalize_region_name(region)

    # aplicar alias
    region_norm = REGION_ALIAS.get(region_norm, region_norm)

    region_map = {
        normalize_region_name(k): k
        for k in data.keys()
    }

    if region_norm not in region_map:
        raise KeyError(
            f"Región '{region}' no encontrada. "
            f"Disponibles: {list(data.keys())}"
        )

    region_key = region_map[region_norm]
    region_data = data[region_key]

    blacklist = {"scaler_center", "scaler_scale", "feature_cols"}

    return {
        "region": region_key,
        "vector_equilibrio": {
            k: v for k, v in region_data.items()
            if k not in blacklist
        }
    }