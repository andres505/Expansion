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
