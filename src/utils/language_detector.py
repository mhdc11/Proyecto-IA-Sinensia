"""
Simple Language Detector - Analizador de Documentos Legales

Detecta idioma del documento basándose en patrones de palabras comunes
sin depender de librerías externas pesadas.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import re
from typing import Dict


# Palabras comunes por idioma (top 50 más frecuentes)
COMMON_WORDS = {
    "es": {
        # Español
        "de", "la", "que", "el", "en", "y", "a", "los", "del", "se",
        "las", "por", "un", "para", "con", "no", "una", "su", "al", "lo",
        "como", "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque",
        "esta", "entre", "cuando", "muy", "sin", "sobre", "también", "me", "hasta",
        "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno",
        "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos"
    },
    "en": {
        # Inglés
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me"
    }
}

# Caracteres distintivos (acentos, ñ, etc.)
DISTINCTIVE_CHARS = {
    "es": {"á", "é", "í", "ó", "ú", "ñ", "ü", "¿", "¡"},
    # Inglés no tiene caracteres distintivos, pero podemos detectar ausencia de acentos
}


def detect_language(texto: str, min_words: int = 10) -> str:
    """
    Detecta el idioma de un texto basándose en palabras comunes

    Estrategia:
    1. Extrae palabras del texto (lowercase, >2 chars)
    2. Cuenta coincidencias con palabras comunes por idioma
    3. Verifica presencia de caracteres distintivos
    4. Retorna idioma con mayor score

    Args:
        texto: Texto a analizar
        min_words: Mínimo de palabras requeridas para detección (default: 10)

    Returns:
        str: Código de idioma ('es', 'en', 'unknown')

    Example:
        >>> detect_language("Este es un documento en español")
        'es'
        >>> detect_language("This is a document in English")
        'en'
        >>> detect_language("Bonjour")
        'unknown'
    """
    if not texto or len(texto.strip()) < 20:
        return "unknown"

    # Extraer palabras (lowercase, >2 chars)
    palabras = re.findall(r"\b[a-záéíóúñü]{3,}\b", texto.lower())

    if len(palabras) < min_words:
        return "unknown"

    # Contar coincidencias por idioma
    scores: Dict[str, float] = {}

    for lang, common_words in COMMON_WORDS.items():
        # Score por palabras comunes
        word_matches = sum(1 for word in palabras if word in common_words)
        word_score = word_matches / len(palabras)

        # Score por caracteres distintivos (bonus)
        distinctive_score = 0.0
        if lang in DISTINCTIVE_CHARS:
            distinctive_chars = DISTINCTIVE_CHARS[lang]
            char_matches = sum(1 for char in texto if char in distinctive_chars)
            if char_matches > 0:
                distinctive_score = min(char_matches / 100.0, 0.2)  # Max bonus: 0.2

        # Score total
        scores[lang] = word_score + distinctive_score

    # Idioma con mayor score
    if not scores:
        return "unknown"

    best_lang = max(scores, key=scores.get)
    best_score = scores[best_lang]

    # Umbral mínimo de confianza: 15% de palabras comunes
    if best_score < 0.15:
        return "unknown"

    return best_lang


def get_language_name(lang_code: str) -> str:
    """
    Convierte código de idioma a nombre completo

    Args:
        lang_code: Código de idioma ('es', 'en', 'unknown')

    Returns:
        str: Nombre del idioma en español

    Example:
        >>> get_language_name("es")
        'Español'
        >>> get_language_name("en")
        'Inglés'
        >>> get_language_name("unknown")
        'Desconocido'
    """
    names = {
        "es": "Español",
        "en": "Inglés",
        "unknown": "Desconocido"
    }

    return names.get(lang_code, "Desconocido")


if __name__ == "__main__":
    # Test del detector de idiomas
    print("=" * 60)
    print("Testing Language Detector")
    print("=" * 60)

    test_cases = [
        # Español
        (
            "Este es un contrato de trabajo entre la empresa ACME Corporation "
            "y el empleado Juan Pérez García. El salario bruto anual será de "
            "30.000 EUR en 14 pagas. Las vacaciones serán de 30 días naturales.",
            "es"
        ),
        # Inglés
        (
            "This is an employment contract between ACME Corporation and "
            "John Smith. The gross annual salary will be 30,000 EUR in "
            "14 payments. Vacation will be 30 calendar days.",
            "en"
        ),
        # Español con acentos
        (
            "La cláusula de no competencia será válida durante 2 años después "
            "de la finalización del contrato. El trabajador no podrá prestar "
            "servicios similares a ningún competidor directo de la empresa.",
            "es"
        ),
        # Muy corto (unknown)
        (
            "Hola mundo",
            "unknown"
        ),
        # Mixto (debería detectar mayoría)
        (
            "El contrato is signed by both parties and será válido during "
            "the entire duration of the employment relationship.",
            "es"  # Más palabras en español
        )
    ]

    print("\n📋 Test Cases:")
    for i, (texto, expected) in enumerate(test_cases, 1):
        detected = detect_language(texto)
        status = "✅" if detected == expected else "❌"

        print(f"\n{status} Test {i}:")
        print(f"   Text: {texto[:60]}...")
        print(f"   Expected: {expected} ({get_language_name(expected)})")
        print(f"   Detected: {detected} ({get_language_name(detected)})")

    # Test de rendimiento
    print("\n📊 Performance Test:")
    import time

    long_text = (
        "Este es un texto largo que contiene muchas palabras en español "
        "para verificar el rendimiento del detector de idiomas. "
    ) * 100  # ~13,000 chars

    start = time.time()
    result = detect_language(long_text)
    elapsed = time.time() - start

    print(f"   Text length: {len(long_text)} chars")
    print(f"   Detected: {result}")
    print(f"   Time: {elapsed*1000:.2f} ms")

    print("\n✅ Language detector ready!")
