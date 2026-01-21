from datetime import datetime
from typing import Dict, Any


def build_payload_flat(
    *,
    lat: float,
    lon: float,

    # metadata
    fuente: str = "expansion_pipeline_v1",

    # NETO
    neto_data: Dict[str, Any],

    # INEGI (YA con llaves INEGI_*)
    inegi_data: Dict[str, Any],

    # GOOGLE PLACES (conteos planos)
    places_count: Dict[str, Any],

    # COMPETENCIA (incluye counts + columnas por cadena)
    competencia_data: Dict[str, Any],
):
    """
    Construye el payload FINAL, PLANO y legacy-compatible.
    """

    payload = {
        # --------------------------------------------------
        # METADATA
        # --------------------------------------------------
        "timestamp": datetime.utcnow().isoformat(),
        "fuente": fuente,
        "lat": lat,
        "longitud": lon,

        # --------------------------------------------------
        # ESTADO / REGION (desde tienda cercana)
        # --------------------------------------------------
        "estado": neto_data.get("estado"),
        "region": neto_data.get("region"),
    }

    # --------------------------------------------------
    # TIENDA NETO CERCANA (PLANO)
    # --------------------------------------------------
    payload.update({
        "id_tienda_cercana": neto_data.get("id_tienda_cercana"),
        "distancia_tienda_cercana_km": neto_data.get("distancia_tienda_cercana_km"),

        "tienda_cercanaExistencia_Costo": neto_data.get("tienda_cercanaExistencia_Costo"),
        "tienda_cercanaExistencia_Piezas": neto_data.get("tienda_cercanaExistencia_Piezas"),
        "tienda_cercanaVenta_Sin_Impuestos": neto_data.get("tienda_cercanaVenta_Sin_Impuestos"),
        "tienda_cercanaVenta_Costo": neto_data.get("tienda_cercanaVenta_Costo"),
        "tienda_cercanaVenta_Piezas": neto_data.get("tienda_cercanaVenta_Piezas"),
        "tienda_cercanaTransacciones": neto_data.get("tienda_cercanaTransacciones"),
        "tienda_cercanaTicket_Promedio": neto_data.get("tienda_cercanaTicket_Promedio"),
        "tienda_cercanaProm_Cantidad": neto_data.get("tienda_cercanaProm_Cantidad"),
        "tienda_cercanaProm_Monto_Sin_Imp": neto_data.get("tienda_cercanaProm_Monto_Sin_Imp"),
    })

    # --------------------------------------------------
    # INEGI (YA PREFIJADO)
    # --------------------------------------------------
    payload.update(inegi_data)

    # --------------------------------------------------
    # GOOGLE PLACES (conteos planos)
    # --------------------------------------------------
    payload.update(places_count)

    # --------------------------------------------------
    # COMPETENCIA (counts + columnas por cadena)
    # --------------------------------------------------
    payload.update(competencia_data)

    return payload
