import json
import os
from typing import Dict, Any
from openai import OpenAI

from expansion.prompt_builder import build_expansion_prompt_semaforo_v12


# --------------------------------------------------
# Cliente OpenAI (GLOBAL DEL MÓDULO)
# --------------------------------------------------
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


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
                "content": """
Eres un analista senior de expansión retail hard-discount.
Debes responder exclusivamente con JSON válido, sin texto adicional.

IMPORTANTE – USO DE TIENDA CERCANA

Cuando exista una tienda NETO cercana, el ÚNICO dato válido y permitido
para evaluar su desempeño es: "Prom. monto sin imp.".

Si no existe, ignóralo completamente.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("```").strip()

    output = json.loads(raw)

    output["decision"] = output["decision"].strip().upper()
    output["explicacion"] = output["explicacion"].strip()

    assert output["decision"] in ["DESCARTAR", "EVALUAR", "AVANZAR"]

    return output
