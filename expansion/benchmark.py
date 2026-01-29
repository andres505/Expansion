# expansion/benchmark.py

import pandas as pd
import numpy as np


# ======================================================
# HELPERS
# ======================================================
def _safe_div(site, ideal):
    """
    División segura para calcular delta relativo.
    """
    try:
        if site is None or ideal is None:
            return None
        if isinstance(ideal, str):
            return None
        if ideal == 0 or pd.isna(ideal):
            return None
        return (site - ideal) / ideal
    except Exception:
        return None


def _fmt_val(x):
    """
    Formato bonito para valores numéricos.
    """
    if x is None or pd.isna(x):
        return "-"
    if isinstance(x, (int, float)):
        if abs(x) >= 1_000_000:
            return f"{x:,.0f}"
        if abs(x) >= 1_000:
            return f"{x:,.0f}"
        return round(x, 2)
    return x


def _fmt_delta(x):
    """
    Formato bonito para el delta porcentual.
    """
    if x is None or pd.isna(x):
        return "-"
    return f"{int(round(x * 100))}%"


# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================
def build_region_benchmark_table(
    payload: dict,
    region_vector: dict,
    variables_map: dict | None = None
) -> pd.DataFrame:
    """
    Construye tabla comparativa:
    Sitio evaluado vs Benchmark regional (perfil_equilibrio)

    - payload: dict plano del sitio
    - region_vector: dict con profile_equilibrio
    - variables_map: mapping explícito (opcional)
    """

    # ==================================================
    # PERFIL REGIONAL
    # ==================================================
    profile_eq = (
        region_vector
        .get("vector_equilibrio", {})
        .get("profile_equilibrio", {})
    )

    # ==================================================
    # VARIABLES DEFAULT (alineadas 100%)
    # ==================================================
    if variables_map is None:
        variables_map = {

            # -----------------------
            # DEMOGRAFÍA
            # -----------------------
            "Población total": {
                "payload": "INEGI_POB_TOTAL_CENSO_2020",
                "vector": "Poblacion Total"
            },
            "Hogares": {
                "payload": "INEGI_hogares",
                "vector": "INEGI_hogares"
            },

            # -----------------------
            # GENERADORES COMERCIALES
            # -----------------------
            "Generadores comerciales totales": {
                "payload": "generadores_total",
                "vector": "total_lugares"
            },
            "Escuelas": {
                "payload": "generadores_educacion_count",
                "vector": "primary_school"
            },
            "Hospitales": {
                "payload": "generadores_salud_count",
                "vector": "hospital"
            },
            "Restaurantes": {
                "payload": "generadores_consumo_count",
                "vector": "restaurant"
            },

            # -----------------------
            # COMPETENCIA
            # -----------------------
            "Competencia total": {
                "payload": "competencia_total",
                "vector": None
            },
            "Tiendas 3B": {
                "payload": "competencia_tiendas_3b",
                "vector": "TIENDAS_3B"
            },
            "Bodega Aurrera": {
                "payload": "competencia_bodega_aurrera",
                "vector": None
            },

            # -----------------------
            # INTEGRACIÓN COMERCIAL
            # -----------------------
            "Integración comercial": {
                "payload": "integracion_score",
                "vector": "__HARDCODE_80__"
            }
        }

    rows = []

    # ==================================================
    # CONSTRUCCIÓN DE TABLA
    # ==================================================
    for label, cfg in variables_map.items():
        payload_key = cfg.get("payload")
        vector_key = cfg.get("vector")

        # -----------------------
        # Valor sitio
        # -----------------------
        site_val = payload.get(payload_key)

        # -----------------------
        # Valor benchmark
        # -----------------------
        if vector_key == "__HARDCODE_80__":
            ideal_val = 80
        elif vector_key is None:
            ideal_val = "-"
        else:
            ideal_val = profile_eq.get(vector_key)

        # -----------------------
        # Delta
        # -----------------------
        delta = _safe_div(site_val, ideal_val)
        delta_fmt = _fmt_delta(delta)

        rows.append({
            "Variable": label,
            "Benchmark regional": _fmt_val(ideal_val),
            "Sitio": _fmt_val(site_val),
            "Δ vs benchmark": delta_fmt
        })

    df = pd.DataFrame(rows)

    return df