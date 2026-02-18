"""
Text Normalization - Analizador de Documentos Legales

Utilidades para normalizar texto extraído de documentos,
limpiando espacios, saltos de línea y caracteres de control.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import re
from typing import Optional


def normalize_text(
    raw: str, max_length: Optional[int] = None, preserve_structure: bool = True
) -> str:
    """
    Normaliza texto extraído limpiando espacios, saltos de línea y caracteres de control

    Args:
        raw: Texto sin procesar
        max_length: Longitud máxima del texto (trunca si excede, None = sin límite)
        preserve_structure: Si True, preserva estructura básica de párrafos (saltos dobles)

    Returns:
        str: Texto normalizado y limpio

    Example:
        >>> raw = "Texto   con\\n\\nespacios     múltiples\\n\\n\\ny saltos"
        >>> normalized = normalize_text(raw)
        >>> print(normalized)
        'Texto con\\n\\nespacios múltiples\\n\\ny saltos'
    """
    if not raw:
        return ""

    # 1. Eliminar caracteres de control (excepto \n y \t si preserve_structure)
    if preserve_structure:
        # Mantener solo \n, \t, y caracteres imprimibles
        text = "".join(char for char in raw if char.isprintable() or char in "\n\t")
    else:
        # Mantener solo caracteres imprimibles (sin \n, \t)
        text = "".join(char for char in raw if char.isprintable())

    # 2. Normalizar espacios en blanco (múltiples espacios → uno solo)
    text = re.sub(r"[ \t]+", " ", text)

    # 3. Normalizar saltos de línea
    if preserve_structure:
        # Múltiples saltos de línea (>3) → máximo 2 (párrafo)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Salto de línea simple + espacios → salto simple limpio
        text = re.sub(r"\n +", "\n", text)
    else:
        # Reemplazar todos los saltos de línea por espacios
        text = text.replace("\n", " ")
        # Normalizar espacios resultantes
        text = re.sub(r" {2,}", " ", text)

    # 4. Eliminar espacios al inicio y final
    text = text.strip()

    # 5. Truncar si excede max_length
    if max_length and len(text) > max_length:
        # Truncar sin cortar palabras
        text = text[:max_length].rsplit(" ", 1)[0] + "..."

    return text


def remove_page_markers(text: str) -> str:
    """
    Elimina marcadores de página insertados por extractores

    Args:
        text: Texto con marcadores de página (ej: "--- Página 1 ---")

    Returns:
        str: Texto sin marcadores

    Example:
        >>> text = "Texto\\n--- Página 1 ---\\nMás texto"
        >>> clean = remove_page_markers(text)
        >>> print(clean)
        'Texto\\nMás texto'
    """
    # Eliminar líneas que contienen "--- Página N ---" o "--- Página N (OCR) ---"
    text = re.sub(r"---\s*Página\s+\d+\s*(\(OCR\))?\s*---", "", text)
    # Limpiar saltos de línea múltiples resultantes
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_ocr_artifacts(text: str) -> str:
    """
    Limpia artefactos comunes de OCR (caracteres extraños, mal reconocidos)

    Args:
        text: Texto con posibles artefactos de OCR

    Returns:
        str: Texto limpio

    Example:
        >>> ocr_text = "Contrato ||abora| del 2024"
        >>> clean = clean_ocr_artifacts(ocr_text)
        >>> print(clean)
        'Contrato laboral del 2024'
    """
    # Diccionario de reemplazos comunes de OCR
    replacements = {
        "||": "l",  # Doble pipe → l
        "|": "l",  # Pipe → l (común en OCR)
        "0": "O",  # Cero → O mayúscula (en contexto de palabras)
        "1": "l",  # Uno → l (en contexto)
    }

    # Aplicar reemplazos contextualmente (solo dentro de palabras)
    for bad, good in replacements.items():
        # Reemplazar solo si está rodeado de letras
        pattern = r"(?<=[a-zA-Z])" + re.escape(bad) + r"(?=[a-zA-Z])"
        text = re.sub(pattern, good, text)

    return text


def extract_first_n_words(text: str, n: int = 100) -> str:
    """
    Extrae las primeras N palabras del texto (útil para previews)

    Args:
        text: Texto completo
        n: Número de palabras a extraer

    Returns:
        str: Primeras N palabras con "..." al final

    Example:
        >>> text = "Este es un texto largo con muchas palabras..."
        >>> preview = extract_first_n_words(text, n=5)
        >>> print(preview)
        'Este es un texto largo...'
    """
    words = text.split()
    if len(words) <= n:
        return text
    return " ".join(words[:n]) + "..."


if __name__ == "__main__":
    # Test de normalización de texto
    print("=" * 60)
    print("Testing Text Normalization")
    print("=" * 60)

    # Test 1: Normalización básica
    print("\n📋 Test 1: Basic normalization")
    raw = """
    Este    es   un   texto


    con   espacios    múltiples



    y saltos    de línea     excesivos
    """
    normalized = normalize_text(raw)
    print(f"Original length: {len(raw)}")
    print(f"Normalized length: {len(normalized)}")
    print(f"Normalized:\n{normalized}")

    # Test 2: Sin preservar estructura
    print("\n📋 Test 2: Without structure preservation")
    normalized_flat = normalize_text(raw, preserve_structure=False)
    print(f"Flattened: {normalized_flat}")

    # Test 3: Truncado
    print("\n📋 Test 3: Truncation")
    long_text = "Palabra " * 100
    truncated = normalize_text(long_text, max_length=50)
    print(f"Truncated (max 50 chars): {truncated}")
    print(f"Length: {len(truncated)}")

    # Test 4: Eliminar marcadores de página
    print("\n📋 Test 4: Remove page markers")
    text_with_markers = """
    Texto de página 1
    --- Página 1 ---
    Texto de página 2
    --- Página 2 (OCR) ---
    Texto de página 3
    """
    clean = remove_page_markers(text_with_markers)
    print(f"Cleaned:\n{clean}")

    # Test 5: Limpiar artefactos de OCR
    print("\n📋 Test 5: Clean OCR artifacts")
    ocr_text = "Contrato ||abora| del 2024 con sue|do mensual"
    clean_ocr = clean_ocr_artifacts(ocr_text)
    print(f"Original OCR: {ocr_text}")
    print(f"Cleaned: {clean_ocr}")

    # Test 6: Extraer primeras N palabras
    print("\n📋 Test 6: Extract first N words")
    text = "Este es un contrato laboral entre ACME Corp y Juan Pérez con salario de 30000 euros"
    preview = extract_first_n_words(text, n=8)
    print(f"Preview (8 words): {preview}")

    print("\n✅ All normalization tests passed!")
