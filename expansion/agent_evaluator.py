# expansion/agent_evaluator.py

import json
import os
from typing import Dict, Any
from openai import OpenAI

from expansion.prompt_builder import build_expansion_prompt_semaforo_v12

# ======================================================
# OpenAI Client (GLOBAL, UNA SOLA VEZ)
# ======================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY no está definida en variables de entorno")

client = OpenAI(api_key=OPENAI_API_KEY)

# ======================================================
# EJECUCIÓN SEGURA DEL AGENTE
# ======================================================
def _run_agent(prompt: str) -> Dict[str, Any]:
    """
    Ejecuta el modelo LLM y devuelve JSON normalizado.
    """
    response = client.chat.completions.create(
        model="gpt-4.1",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista senior de expansión retail hard-discount.\n"
                    "Debes responder exclusivamente con JSON válido.\n\n"
                    "IMPORTANTE – USO DE TIENDA CERCANA\n"
                    "Cuando exista una tienda NETO cercana, el ÚNICO dato válido\n"
                    "para evaluar su desempeño es: 'Prom. monto sin imp.'\n"
                    "Si no está disponible, ignora la tienda cercana."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Limpieza defensiva
    if raw.startswith("```"):
        raw = raw.strip("```").strip()

    output = json.loads(raw)

    # Normalización mínima
    output["decision"] = output["decision"].strip().upper()
    output["explicacion"] = output["explicacion"].strip()

    if output["decision"] not in {"AVANZAR", "EVALUAR", "DESCARTAR"}:
        raise ValueError(f"Decisión inválida del agente: {output['decision']}")

    return output


# ======================================================
# FUNCIÓN PÚBLICA (LA QUE IMPORTA MAIN)
# ======================================================
def evaluate_site_dual(
    *,
    payload: dict,
    region_vector: dict,
    tabla_global: Any,
    tabla_maduras: Any,
) -> Dict[str, Any]:
    """
    Ejecuta dos evaluaciones independientes del mismo sitio
    y devuelve decisiones planas, listas para API / BQ.
    """

    # -------------------------
    # Evaluación 1
    # -------------------------
    prompt_1 = build_expansion_prompt_semaforo_v12(
        payload=payload,
        region_vector=region_vector,
        tabla_global=tabla_global,
        tabla_maduras=tabla_maduras,
    )

    eval_1 = _run_agent(prompt_1)

    # -------------------------
    # Evaluación 2 (razonamiento independiente)
    # -------------------------
    prompt_2 = build_expansion_prompt_semaforo_v12(
        payload=payload,
        region_vector=region_vector,
        tabla_global=tabla_global,
        tabla_maduras=tabla_maduras,
    )

    eval_2 = _run_agent(prompt_2)

    # -------------------------
    # Salida FINAL (API-friendly)
    # -------------------------
    return {
        "decision_modelo_1": eval_1["decision"],
        "explicacion_modelo_1": eval_1["explicacion"],
        "decision_modelo_2": eval_2["decision"],
        "explicacion_modelo_2": eval_2["explicacion"],
        "decision_consenso": (
            eval_1["decision"]
            if eval_1["decision"] == eval_2["decision"]
            else "EVALUAR"
        ),
    }
