"""
Document Classifier - Analizador de Documentos Legales

Clasificación mejorada de documentos con heurísticas basadas en keywords.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import re
from typing import Dict, List, Tuple, Optional


# Keywords por tipo de documento
DOCUMENT_TYPE_KEYWORDS = {
    "contrato_laboral": [
        "contrato de trabajo",
        "contrato laboral",
        "trabajador",
        "empleador",
        "salario",
        "jornada laboral",
        "vacaciones",
        "despido",
        "periodo de prueba",
        "convenio colectivo"
    ],
    "nomina": [
        "nómina",
        "recibo de salarios",
        "percepciones",
        "deducciones",
        "bases de cotización",
        "irpf",
        "seguridad social",
        "líquido a percibir",
        "base reguladora"
    ],
    "convenio": [
        "convenio colectivo",
        "representantes de los trabajadores",
        "ámbito de aplicación",
        "clasificación profesional",
        "tabla salarial",
        "jornada anual"
    ],
    "certificado": [
        "certifica que",
        "se expide el presente certificado",
        "en uso de las atribuciones",
        "para que conste",
        "a petición del interesado"
    ],
    "poder_notarial": [
        "poder notarial",
        "otorga poder",
        "ante mí",
        "comparece",
        "representación",
        "mandato",
        "notario",
        "protocolo"
    ],
    "acta": [
        "acta de la reunión",
        "asistentes",
        "orden del día",
        "acuerdos adoptados",
        "se levanta la sesión"
    ],
    "contrato_arrendamiento": [
        "contrato de arrendamiento",
        "arrendador",
        "arrendatario",
        "alquiler",
        "fianza",
        "renta mensual",
        "inmueble"
    ],
    "contrato_compraventa": [
        "contrato de compraventa",
        "vendedor",
        "comprador",
        "precio",
        "transmite la propiedad",
        "bien inmueble",
        "mueble"
    ],
}


def classify_document_by_keywords(texto: str) -> Tuple[str, float]:
    """
    Clasifica documento según presencia de keywords

    Args:
        texto: Texto completo del documento (normalizado)

    Returns:
        Tuple de (tipo_documento, confianza)
        - tipo_documento: string con el tipo detectado
        - confianza: float 0.0-1.0 indicando nivel de certeza

    Examples:
        >>> classify_document_by_keywords("Este contrato laboral establece...")
        ('contrato_laboral', 0.85)
    """
    texto_lower = texto.lower()

    # Contar matches por tipo
    scores: Dict[str, int] = {}

    for doc_type, keywords in DOCUMENT_TYPE_KEYWORDS.items():
        matches = sum(1 for keyword in keywords if keyword in texto_lower)
        if matches > 0:
            scores[doc_type] = matches

    # Si no hay matches, retornar desconocido
    if not scores:
        return ("desconocido", 0.0)

    # Ordenar por score
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Tipo con mayor score
    best_type, best_score = sorted_types[0]

    # Calcular confianza (normalizada)
    max_possible_keywords = len(DOCUMENT_TYPE_KEYWORDS[best_type])
    confianza = min(best_score / max_possible_keywords, 1.0)

    # Ajustar confianza si hay tipos competidores cercanos
    if len(sorted_types) > 1:
        second_score = sorted_types[1][1]
        if second_score / best_score > 0.7:  # Competidor cercano
            confianza *= 0.8  # Penalizar por ambigüedad

    return (best_type, confianza)


def refine_document_type(llm_type: str, texto: str) -> Tuple[str, float]:
    """
    Refina el tipo de documento detectado por el LLM usando heurísticas

    Args:
        llm_type: Tipo detectado por el LLM
        texto: Texto completo del documento

    Returns:
        Tuple de (tipo_refinado, confianza)
    """
    # Clasificar con keywords
    keyword_type, keyword_conf = classify_document_by_keywords(texto)

    # Si LLM y keywords coinciden, alta confianza
    if llm_type == keyword_type:
        return (llm_type, min(keyword_conf + 0.15, 1.0))  # Boost de confianza

    # Si el LLM dice "desconocido" pero keywords detectan algo
    if llm_type == "desconocido" and keyword_type != "desconocido":
        return (keyword_type, keyword_conf)

    # Si hay conflicto, priorizar el que tenga mayor confianza
    # (Asumir que LLM tiene confianza base de 0.7 si no es desconocido)
    llm_confidence = 0.7 if llm_type != "desconocido" else 0.0

    if keyword_conf > llm_confidence:
        return (keyword_type, keyword_conf)
    else:
        return (llm_type, llm_confidence)


def extract_document_metadata(texto: str) -> Dict[str, any]:
    """
    Extrae metadata adicional del documento

    Args:
        texto: Texto completo

    Returns:
        Dict con metadata detectada
    """
    metadata = {
        "has_signatures": False,
        "has_stamps": False,
        "has_tables": False,
        "language_indicators": []
    }

    texto_lower = texto.lower()

    # Detectar firmas
    signature_patterns = [
        r'fdo\.',
        r'firmado',
        r'firma',
        r'signatura'
    ]
    metadata["has_signatures"] = any(
        re.search(pattern, texto_lower) for pattern in signature_patterns
    )

    # Detectar sellos
    stamp_patterns = [
        r'sello',
        r'registro',
        r'certificado'
    ]
    metadata["has_stamps"] = any(
        re.search(pattern, texto_lower) for pattern in stamp_patterns
    )

    # Detectar tablas (heurística básica)
    # Buscar múltiples líneas con separadores tabulares
    lines = texto.split('\n')
    table_indicators = sum(1 for line in lines if '\t' in line or '|' in line)
    metadata["has_tables"] = table_indicators > 3

    # Indicadores de idioma
    if "artículo" in texto_lower or "cláusula" in texto_lower:
        metadata["language_indicators"].append("español_legal")

    if "whereas" in texto_lower or "hereinafter" in texto_lower:
        metadata["language_indicators"].append("inglés_legal")

    return metadata


if __name__ == "__main__":
    # Test de clasificación
    print("=== Test de Clasificación de Documentos ===\n")

    test_docs = [
        ("Este contrato de trabajo establece las condiciones entre empleador y trabajador...",
         "contrato_laboral"),

        ("Nómina del mes de enero. Percepciones: salario base, IRPF, Seguridad Social...",
         "nomina"),

        ("El presente poder notarial otorga mandato ante mí, el notario...",
         "poder_notarial"),

        ("Este documento no tiene keywords claras",
         "desconocido")
    ]

    for texto, expected in test_docs:
        detected_type, confidence = classify_document_by_keywords(texto)
        match = "✅" if detected_type == expected else "❌"
        print(f"{match} Esperado: {expected:20s} | Detectado: {detected_type:20s} | Confianza: {confidence:.2f}")
        print(f"   Texto: {texto[:60]}...")
        print()

    print("\n✅ Document Classifier ready!")
