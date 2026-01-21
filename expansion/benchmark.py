# expansion/benchmark.py
import numpy as np
import pandas as pd


def _safe_number(x):
    if isinstance(x, list):
        return x[0] if x else np.nan
    if isinstance(x, (int, float)):
        return x
    return np.nan


def build_region_benchmark_table(
    *,
    payload: dict,
    region_vector: dict,
    variables_map: dict
) -> pd.DataFrame:
    """
    Construye tabla comparativa:
    Sitio vs Benchmark regional (vector de equilibrio)
    """

    profile = region_vector["vector_equilibrio"]["profile_equilibrio"]
    rows = []

    for label, cfg in variables_map.items():
        v_key = cfg["vector"]
        p_key = cfg["payload"]

        punto_val = _safe_number(payload.get(p_key))
        bench_val = _safe_number(profile.get(v_key))

        if pd.notna(bench_val) and bench_val != 0 and pd.notna(punto_val):
            delta = (punto_val - bench_val) / bench_val * 100
        else:
            delta = np.nan

        rows.append({
            "Variable": label,
            "Benchmark regional": round(bench_val) if pd.notna(bench_val) else np.nan,
            "Punto candidato": round(punto_val) if pd.notna(punto_val) else np.nan,
            "Δ vs benchmark (%)": round(delta) if pd.notna(delta) else np.nan
        })

    return pd.DataFrame(rows)
