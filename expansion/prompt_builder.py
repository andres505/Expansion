# expansion/prompt_builder.py

from typing import Dict, Any
import json


# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================
def build_expansion_prompt_semaforo_v12(
    *,
    payload: Dict[str, Any],
    region_vector: Dict[str, Any],
    tabla_global: Any,
    tabla_maduras: Any,
) -> str:
    """
    Construye el prompt completo para evaluación de expansión
    bajo lógica de semáforo (AVANZAR / EVALUAR / DESCARTAR).

    Este módulo:
    - NO ejecuta modelos
    - NO importa otros módulos del pipeline
    - SOLO genera texto
    """

    sections = [
        _build_header(),
        _build_region_context(region_vector),
        _build_payload_context(payload),
        _build_benchmarks_context(tabla_global, tabla_maduras),
        _build_decision_rules(),
        _build_output_schema(),
    ]

    return "\n\n".join(sections)


# ======================================================
# SECCIONES DEL PROMPT
# ======================================================
def _build_header() -> str:
    return (
        "Eres un analista senior de expansión retail hard-discount.\n"
        "Tu objetivo es evaluar un sitio candidato para apertura de tienda "
        "y emitir una recomendación ejecutiva clara y justificada."
    )


def _build_region_context(region_vector: Dict[str, Any]) -> str:
    return (
        "CONTEXTO REGIONAL:\n"
        f"Región evaluada: {region_vector.get('region', '-')}\n\n"
        "Vector de equilibrio regional (referencia de desempeño esperado):\n"
        f"{json.dumps(region_vector.get('vector_equilibrio', {}), indent=2, ensure_ascii=False)}"
    )


def _build_payload_context(payload: Dict[str, Any]) -> str:
    return (
        "DATOS DEL SITIO CANDIDATO:\n"
        "La siguiente información describe el punto propuesto, su entorno "
        "demográfico, competitivo y operativo.\n\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )


def _build_benchmarks_context(tabla_global: Any, tabla_maduras: Any) -> str:
    return (
        "BENCHMARKS DE REFERENCIA:\n\n"
        "Comparativos globales:\n"
        f"{tabla_global}\n\n"
        "Comparativos de tiendas maduras:\n"
        f"{tabla_maduras}"
    )


def _build_decision_rules() -> str:
    return (
        "CRITERIOS DE DECISIÓN (SEMÁFORO):\n"
        "- AVANZAR: El sitio muestra alto potencial de demanda, "
        "condiciones favorables y riesgos controlados.\n"
        "- EVALUAR: El sitio presenta señales mixtas, incertidumbre "
        "operativa o requiere validaciones adicionales.\n"
        "- DESCARTAR: El sitio tiene bajo potencial, saturación competitiva "
        "o riesgos elevados que comprometen la rentabilidad."
    )


def _build_output_schema() -> str:
    return (
        "FORMATO DE RESPUESTA (OBLIGATORIO):\n"
        "Debes responder EXCLUSIVAMENTE en JSON válido, sin texto adicional.\n\n"
        "{\n"
        '  "decision": "AVANZAR | EVALUAR | DESCARTAR",\n'
        '  "explicacion": "Explicación ejecutiva clara, concisa y orientada a toma de decisión"\n'
        "}\n\n"
        "NO agregues comentarios, encabezados ni texto fuera del JSON."
    )
