import json
from typing import Dict, Any
from openai import OpenAI

from expansion.prompt_builder import build_expansion_prompt_semaforo_v12


# --------------------------------------------------
# Cliente OpenAI
# --------------------------------------------------
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



# --------------------------------------------------
# Función interna segura para ejecutar el agente
# --------------------------------------------------
def _run_agent(prompt: str) -> Dict[str, Any]:
    response = client.chat.completions.create(
        model="gpt-4.1",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista senior de expansión retail hard-discount. "
                    "Debes responder exclusivamente con JSON válido, sin texto adicional."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw = response.choices[0].message.content.strip()

    # Limpieza defensiva
    if raw.startswith("```"):
        raw = raw.strip("```").strip()

    output = json.loads(raw)

    # Normalización
    output["decision"] = output["decision"].strip().upper()
    output["explicacion"] = output["explicacion"].strip()

    # Validaciones mínimas
    assert output["decision"] in ["DESCARTAR", "EVALUAR", "AVANZAR"]
    assert isinstance(output["explicacion"], str)

    return output


# --------------------------------------------------
# FUNCIÓN PÚBLICA: DOS EVALUACIONES
# --------------------------------------------------
def evaluate_site_dual(
    *,
    payload: dict,
    region_vector: dict,
    tabla_global: dict,
    tabla_maduras: dict
) -> Dict[str, Any]:
    """
    Ejecuta dos evaluaciones independientes del agente.
    Retorna salida plana y legacy-compatible.
    """

    # -------------------------------
    # Evaluación 1 – estándar
    # -------------------------------
    prompt_1 = build_expansion_prompt_semaforo_v12(
        payload=payload,
        region_vector=region_vector,
        tabla_global=tabla_global,
        tabla_maduras=tabla_maduras
    )

    eval_1 = _run_agent(prompt_1)

    # -------------------------------
    # Evaluación 2 – contraste
    # (misma data, razonamiento independiente)
    # -------------------------------
    prompt_2 = build_expansion_prompt_semaforo_v12(
        payload=payload,
        region_vector=region_vector,
        tabla_global=tabla_global,
        tabla_maduras=tabla_maduras
    )

    eval_2 = _run_agent(prompt_2)

    # -------------------------------
    # Salida final
    # -------------------------------
    return {
        "decision_modelo_1": eval_1["decision"],
        "explicacion_1": eval_1["explicacion"],

        "decision_modelo_2": eval_2["decision"],
        "explicacion_2": eval_2["explicacion"]
    }
