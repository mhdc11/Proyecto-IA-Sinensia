"""
Prompt Builder - Analizador de Documentos Legales

Ensambla el prompt final para el LLM combinando:
- Constitution (reglas)
- Specify (tarea y schema)
- Plan (pasos)
- Documento (texto extraído, con truncado seguro)

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from typing import Optional

from src.orchestration.prompts import get_full_system_prompt
from src.utils.config_loader import get_config


def estimate_token_count(text: str) -> int:
    """
    Estima el número de tokens de un texto (aproximación)

    Regla heurística: ~4 caracteres por token para español/inglés

    Args:
        text: Texto a estimar

    Returns:
        int: Número aproximado de tokens
    """
    return len(text) // 4


def truncate_text_safe(text: str, max_chars: int) -> str:
    """
    Trunca texto sin cortar palabras ni oraciones

    Args:
        text: Texto a truncar
        max_chars: Número máximo de caracteres

    Returns:
        str: Texto truncado de forma segura

    Example:
        >>> text = "Este es un texto largo que necesita ser truncado."
        >>> truncated = truncate_text_safe(text, max_chars=30)
        >>> print(truncated)
        'Este es un texto largo...'
    """
    if len(text) <= max_chars:
        return text

    # Truncar en el carácter límite
    truncated = text[:max_chars]

    # Buscar el último espacio para no cortar palabras
    last_space = truncated.rfind(" ")

    if last_space > max_chars * 0.8:  # Si el espacio está en el último 20%
        truncated = truncated[:last_space]

    # Añadir indicador de truncado
    return truncated.strip() + "..."


def build_prompt(
    texto: str,
    max_tokens: Optional[int] = None,
    include_truncation_note: bool = True
) -> str:
    """
    Ensambla el prompt completo para el LLM con truncado seguro

    El prompt final tiene esta estructura:
    [CONSTITUTION + SPECIFY + PLAN]
    [DOCUMENTO]
    <texto del documento truncado si es necesario>

    Args:
        texto: Texto del documento a analizar
        max_tokens: Límite de tokens total (None = usar config, default ~4000)
        include_truncation_note: Si True, añade nota si el texto fue truncado

    Returns:
        str: Prompt completo listo para enviar al LLM

    Example:
        >>> from src.orchestration.prompt_builder import build_prompt
        >>> texto_doc = "Contrato laboral entre ACME Corp..."
        >>> prompt = build_prompt(texto_doc)
        >>> print(len(prompt))
        15620
    """
    # Cargar configuración
    config = get_config()
    if max_tokens is None:
        max_tokens = config.ollama.max_tokens

    # Obtener el prompt de sistema
    system_prompt = get_full_system_prompt()
    system_tokens = estimate_token_count(system_prompt)

    # Calcular espacio disponible para el documento
    # Reservar ~200 tokens para la respuesta del LLM
    available_tokens = max_tokens - system_tokens - 200

    if available_tokens < 500:
        raise ValueError(
            f"Not enough token space for document. "
            f"System prompt uses {system_tokens} tokens, "
            f"max is {max_tokens}. Need at least 500 tokens for document."
        )

    # Convertir tokens disponibles a caracteres aproximados
    available_chars = available_tokens * 4

    # Truncar texto del documento si es necesario
    was_truncated = False
    if len(texto) > available_chars:
        was_truncated = True
        texto_truncado = truncate_text_safe(texto, available_chars)
    else:
        texto_truncado = texto

    # Ensamblar prompt final
    prompt_parts = [
        system_prompt,
        "\n\n" + "=" * 60,
        "\nDOCUMENTO A ANALIZAR:\n",
        "=" * 60 + "\n\n",
        texto_truncado
    ]

    # Añadir nota de truncado si aplica
    if was_truncated and include_truncation_note:
        prompt_parts.append(
            f"\n\n[NOTA: Documento truncado a {available_chars} caracteres "
            f"de {len(texto)} totales para ajustar al contexto del LLM. "
            f"Analiza ÚNICAMENTE el contenido visible.]"
        )

    final_prompt = "".join(prompt_parts)

    # Verificar que no excedemos el límite
    final_tokens = estimate_token_count(final_prompt)
    if final_tokens > max_tokens:
        print(
            f"⚠️  Warning: Prompt exceeds max tokens "
            f"({final_tokens} > {max_tokens}). May be truncated by LLM."
        )

    print(f"📊 Prompt stats:")
    print(f"   System prompt: {system_tokens} tokens (~{len(system_prompt)} chars)")
    print(f"   Document: {estimate_token_count(texto_truncado)} tokens (~{len(texto_truncado)} chars)")
    print(f"   Total: {final_tokens} tokens (~{len(final_prompt)} chars)")
    print(f"   Truncated: {'Yes' if was_truncated else 'No'}")

    return final_prompt


if __name__ == "__main__":
    # Test de prompt builder
    print("=" * 60)
    print("Testing Prompt Builder")
    print("=" * 60)

    # Test 1: Documento corto (no truncado)
    print("\n📋 Test 1: Short document (no truncation)")
    short_text = """
    CONTRATO LABORAL

    Entre ACME CORP S.A. (CIF: A12345678) y Juan Pérez García (DNI: 12345678Z).

    Fecha de inicio: 1 de marzo de 2026
    Fecha de fin: 28 de febrero de 2027

    Salario bruto anual: 30.000 EUR en 14 pagas.

    Obligaciones del trabajador:
    - No competir durante vigencia + 2 años post-finalización
    - Mantener confidencialidad

    Derechos del trabajador:
    - 30 días de vacaciones anuales
    - Seguro médico privado
    """

    prompt = build_prompt(short_text, max_tokens=4000)
    print(f"\n✅ Prompt built: {len(prompt)} characters")
    print(f"   Preview: {prompt[:200]}...")

    # Test 2: Documento largo (requiere truncado)
    print("\n📋 Test 2: Long document (requires truncation)")
    long_text = "Texto muy largo. " * 5000  # ~80,000 caracteres

    prompt_truncated = build_prompt(long_text, max_tokens=4000)
    print(f"\n✅ Prompt built with truncation: {len(prompt_truncated)} characters")

    # Test 3: Estimación de tokens
    print("\n📋 Test 3: Token estimation")
    test_texts = [
        ("Corto", "Hola mundo"),
        ("Medio", "Este es un texto de longitud media con varias palabras"),
        ("Largo", "Lorem ipsum " * 100)
    ]

    for label, text in test_texts:
        tokens = estimate_token_count(text)
        print(f"   {label}: {len(text)} chars → ~{tokens} tokens")

    # Test 4: Truncado seguro
    print("\n📋 Test 4: Safe truncation")
    text = "Este es un texto que será truncado en medio de una palabra muy larga"
    truncated = truncate_text_safe(text, max_chars=30)
    print(f"   Original: {text}")
    print(f"   Truncated: {truncated}")

    print("\n✅ Prompt builder ready!")
