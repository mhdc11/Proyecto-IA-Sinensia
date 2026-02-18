"""
JSON Response Parser and Validator - Analizador de Documentos Legales

Parsea y valida respuestas JSON del LLM con Pydantic,
incluyendo lógica de reintentos para corrección de formatos inválidos.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import json
import re
from typing import Tuple, Optional, Callable

from pydantic import ValidationError

from src.models.analisis import Analisis
from src.orchestration.ollama_client import ollama_generate
from src.utils.config_loader import get_config


def extract_json_block(response: str) -> Optional[str]:
    """
    Extrae bloque JSON de una respuesta del LLM

    Busca el primer '{' y el último '}' para extraer solo el JSON,
    ignorando texto antes o después.

    Args:
        response: Respuesta completa del LLM (puede contener texto extra)

    Returns:
        str: JSON extraído, o None si no se encuentra

    Example:
        >>> response = "Aquí está el análisis:\\n{\\\"tipo\\\": \\\"contrato\\\"}\\nEspero que ayude"
        >>> json_str = extract_json_block(response)
        >>> print(json_str)
        '{"tipo": "contrato"}'
    """
    # Buscar primer '{' y último '}'
    first_brace = response.find("{")
    last_brace = response.rfind("}")

    if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
        return None

    # Extraer el bloque JSON
    json_block = response[first_brace : last_brace + 1]
    return json_block


def parse_and_validate(response: str) -> Analisis:
    """
    Parsea respuesta del LLM y valida con Pydantic

    Args:
        response: Respuesta del LLM (texto que debe contener JSON)

    Returns:
        Analisis: Objeto Pydantic validado

    Raises:
        ValueError: Si el JSON no se puede parsear o validar

    Example:
        >>> response = '{"tipo_documento": "contrato", "confianza_aprox": 0.9}'
        >>> analisis = parse_and_validate(response)
        >>> print(analisis.tipo_documento)
        'contrato'
    """
    # 1. Extraer bloque JSON
    json_block = extract_json_block(response)

    if not json_block:
        raise ValueError(
            "No se encontró un bloque JSON válido en la respuesta del LLM. "
            "La respuesta debe contener JSON entre { y }."
        )

    # 2. Parsear JSON string a dict
    try:
        json_dict = json.loads(json_block)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON inválido en la respuesta del LLM: {e}. "
            f"Bloque extraído: {json_block[:200]}..."
        ) from e

    # 3. Validar con Pydantic Analisis schema
    try:
        analisis = Analisis(**json_dict)
        return analisis
    except ValidationError as e:
        # Formatear errores de validación de forma legible
        errors_str = "\n".join([f"  - {err['loc']}: {err['msg']}" for err in e.errors()])
        raise ValueError(
            f"El JSON no cumple con el schema de Análisis:\n{errors_str}"
        ) from e


def retry_with_correction(
    llm_function: Callable[[str, str, float], str],
    model: str,
    original_prompt: str,
    temperature: float,
    max_retries: int = 2
) -> Tuple[Analisis, int]:
    """
    Intenta generar y validar análisis con reintentos automáticos

    Si la primera respuesta tiene JSON inválido, envía un mensaje de corrección
    al LLM pidiendo que devuelva SOLO JSON válido.

    Args:
        llm_function: Función que genera texto (ej: ollama_generate)
        model: Nombre del modelo
        original_prompt: Prompt original completo
        temperature: Temperatura de generación
        max_retries: Número máximo de reintentos (default: 2)

    Returns:
        Tuple[Analisis, int]: (análisis validado, número de intentos usados)

    Raises:
        RuntimeError: Si todos los reintentos fallan

    Example:
        >>> from src.orchestration.ollama_client import ollama_generate
        >>> analisis, attempts = retry_with_correction(
        ...     llm_function=ollama_generate,
        ...     model="llama3.2:3b",
        ...     original_prompt=prompt,
        ...     temperature=0.2,
        ...     max_retries=2
        ... )
    """
    config = get_config()
    max_retries = config.ollama.max_retries

    # Intento 1: Prompt original
    print("🔄 Attempt 1: Calling LLM with original prompt...")
    response = llm_function(model, original_prompt, temperature)

    try:
        analisis = parse_and_validate(response)
        print("✅ Valid JSON on first attempt!")
        return analisis, 1
    except ValueError as e:
        print(f"⚠️  Attempt 1 failed: {e}")

    # Reintentos con mensaje de corrección
    for attempt_num in range(2, max_retries + 2):
        if attempt_num > max_retries + 1:
            break

        print(f"🔄 Attempt {attempt_num}: Sending correction message...")

        # Mensaje de corrección
        correction_prompt = f"""
La respuesta anterior no fue JSON válido o no cumplió con el schema.

ERROR: {str(e)[:300]}

Por favor, devuelve ÚNICAMENTE un JSON válido que siga EXACTAMENTE este schema:

{{
  "tipo_documento": "string",
  "partes": ["string"],
  "fechas": [{{"etiqueta": "string", "valor": "string"}}],
  "importes": [{{"concepto": "string", "valor": number|null, "moneda": "string|null"}}],
  "obligaciones": ["string"],
  "derechos": ["string"],
  "riesgos": ["string"],
  "resumen_bullets": ["string"],
  "notas": ["string"],
  "confianza_aprox": number
}}

NO añadas texto explicativo, SOLO el JSON puro.

Documento original: {original_prompt[-1000:]}
"""

        response = llm_function(model, correction_prompt, temperature)

        try:
            analisis = parse_and_validate(response)
            print(f"✅ Valid JSON on attempt {attempt_num}!")
            return analisis, attempt_num
        except ValueError as e:
            print(f"⚠️  Attempt {attempt_num} failed: {e}")
            continue

    # Si llegamos aquí, todos los reintentos fallaron
    raise RuntimeError(
        f"Failed to get valid JSON after {max_retries + 1} attempts. "
        f"Last error: {e}"
    )


if __name__ == "__main__":
    # Test de parser y validador JSON
    print("=" * 60)
    print("Testing JSON Parser and Validator")
    print("=" * 60)

    # Test 1: JSON válido con texto extra
    print("\n📋 Test 1: Valid JSON with extra text")
    response_with_text = """
    Aquí está el análisis del documento:

    {
      "tipo_documento": "contrato_laboral",
      "partes": ["ACME Corp", "Juan Pérez"],
      "fechas": [{"etiqueta": "Inicio", "valor": "2026-03-01"}],
      "importes": [],
      "obligaciones": ["No competir"],
      "derechos": ["30 días vacaciones"],
      "riesgos": [],
      "resumen_bullets": ["Contrato anual"],
      "notas": [],
      "confianza_aprox": 0.9
    }

    Espero que sea útil.
    """

    try:
        analisis = parse_and_validate(response_with_text)
        print("✅ Parsed and validated successfully")
        print(f"   Type: {analisis.tipo_documento}")
        print(f"   Confidence: {analisis.confianza_aprox}")
    except ValueError as e:
        print(f"❌ Failed: {e}")

    # Test 2: JSON inválido (syntax error)
    print("\n📋 Test 2: Invalid JSON (syntax error)")
    invalid_json = '{"tipo_documento": "contrato", "confianza_aprox": 0.9'  # Missing }

    try:
        analisis = parse_and_validate(invalid_json)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {str(e)[:100]}...")

    # Test 3: JSON válido pero schema inválido
    print("\n📋 Test 3: Valid JSON but invalid schema")
    invalid_schema = '{"tipo_documento": "contrato", "confianza_aprox": 1.5}'  # >1.0

    try:
        analisis = parse_and_validate(invalid_schema)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError (schema): {str(e)[:100]}...")

    # Test 4: Sin JSON en respuesta
    print("\n📋 Test 4: No JSON in response")
    no_json = "Lo siento, no puedo procesar este documento."

    try:
        analisis = parse_and_validate(no_json)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {str(e)[:100]}...")

    print("\n✅ JSON validator ready!")
    print("\n⚠️  Note: retry_with_correction() requires Ollama running")
    print("    Test it with actual LLM calls when Ollama is available")
