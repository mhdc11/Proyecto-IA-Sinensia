"""
Citation Mapper - Analizador de Documentos Legales

Mapea frases extraídas (obligaciones, derechos, riesgos) a su ubicación
en el texto original del documento.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher


class Citation:
    """
    Representa una cita/referencia al texto original

    Attributes:
        text: Texto de la cita
        start_line: Línea de inicio en el documento (1-indexed)
        end_line: Línea de fin
        snippet: Fragmento del texto original (contexto)
        similarity: Score de similitud (0.0-1.0)
    """

    def __init__(
        self,
        text: str,
        start_line: int,
        end_line: int,
        snippet: str,
        similarity: float
    ):
        self.text = text
        self.start_line = start_line
        self.end_line = end_line
        self.snippet = snippet
        self.similarity = similarity

    def __repr__(self):
        return (f"Citation(text='{self.text[:30]}...', "
                f"lines={self.start_line}-{self.end_line}, "
                f"similarity={self.similarity:.2f})")


def normalize_text_for_matching(text: str) -> str:
    """
    Normaliza texto para mejorar matching

    Removes: puntuación extra, espacios múltiples, mayúsculas

    Args:
        text: Texto original

    Returns:
        Texto normalizado
    """
    # Minúsculas
    text = text.lower()

    # Remover puntuación extra (mantener puntos y comas básicas)
    text = re.sub(r'[^\w\s.,;]', ' ', text)

    # Espacios múltiples → espacio simple
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calcula similitud entre dos strings

    Args:
        str1, str2: Strings a comparar

    Returns:
        Score 0.0-1.0
    """
    # Normalizar ambos
    norm1 = normalize_text_for_matching(str1)
    norm2 = normalize_text_for_matching(str2)

    # Usar SequenceMatcher de difflib
    matcher = SequenceMatcher(None, norm1, norm2)
    return matcher.ratio()


def find_citation_in_text(
    phrase: str,
    document_lines: List[str],
    threshold: float = 0.7,
    context_lines: int = 2
) -> Optional[Citation]:
    """
    Busca una frase en el documento y retorna su ubicación

    Args:
        phrase: Frase a buscar
        document_lines: Líneas del documento original
        threshold: Umbral de similitud mínima (0.0-1.0)
        context_lines: Líneas de contexto antes/después

    Returns:
        Citation o None si no se encuentra
    """
    phrase_norm = normalize_text_for_matching(phrase)

    best_match: Optional[Tuple[int, int, float]] = None
    best_score = 0.0

    # Buscar en ventanas de 1-5 líneas
    for window_size in range(1, 6):
        for i in range(len(document_lines) - window_size + 1):
            # Extraer ventana
            window_lines = document_lines[i:i + window_size]
            window_text = ' '.join(window_lines)

            # Calcular similitud
            similarity = calculate_similarity(phrase, window_text)

            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = (i, i + window_size - 1, similarity)

    # Si no hay match, retornar None
    if not best_match:
        return None

    start_line, end_line, similarity = best_match

    # Extraer snippet con contexto
    snippet_start = max(0, start_line - context_lines)
    snippet_end = min(len(document_lines), end_line + context_lines + 1)
    snippet_lines = document_lines[snippet_start:snippet_end]
    snippet = '\n'.join(snippet_lines)

    return Citation(
        text=phrase,
        start_line=start_line + 1,  # 1-indexed
        end_line=end_line + 1,
        snippet=snippet,
        similarity=similarity
    )


def map_phrases_to_citations(
    phrases: List[str],
    document_text: str,
    threshold: float = 0.7
) -> Dict[str, Optional[Citation]]:
    """
    Mapea lista de frases a sus citas en el documento

    Args:
        phrases: Lista de frases (obligaciones, derechos, etc.)
        document_text: Texto completo del documento
        threshold: Umbral de similitud

    Returns:
        Dict mapeando frase → Citation (o None si no encontrada)
    """
    document_lines = document_text.split('\n')

    citations_map = {}

    for phrase in phrases:
        citation = find_citation_in_text(phrase, document_lines, threshold)
        citations_map[phrase] = citation

    return citations_map


def generate_citation_report(citations_map: Dict[str, Optional[Citation]]) -> str:
    """
    Genera reporte legible de citas

    Args:
        citations_map: Mapeo de frases a citas

    Returns:
        String con reporte formateado
    """
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("REPORTE DE CITAS AL DOCUMENTO ORIGINAL")
    report_lines.append("=" * 60)

    found = sum(1 for c in citations_map.values() if c is not None)
    total = len(citations_map)

    report_lines.append(f"\nEncontradas: {found}/{total} ({found/total*100:.0f}%)\n")

    for phrase, citation in citations_map.items():
        report_lines.append(f"📌 Frase: \"{phrase[:60]}...\"")

        if citation:
            report_lines.append(f"   ✅ Ubicación: Líneas {citation.start_line}-{citation.end_line}")
            report_lines.append(f"   🎯 Similitud: {citation.similarity:.0%}")
            report_lines.append(f"   📄 Contexto:")
            report_lines.append(f"      {citation.snippet[:100]}...")
        else:
            report_lines.append("   ❌ No encontrada en el documento")

        report_lines.append("")

    report_lines.append("=" * 60)

    return '\n'.join(report_lines)


if __name__ == "__main__":
    # Test de citation mapping
    print("=== Test de Citation Mapper ===\n")

    # Documento de ejemplo
    document_text = """Contrato de Trabajo

Entre ACME Corporation S.A. y Juan Pérez García.

Cláusula 1: Jornada Laboral
El trabajador cumplirá horario de 9:00 a 18:00 de lunes a viernes.

Cláusula 2: No Competencia
El trabajador se compromete a no competir durante la vigencia del contrato
y durante dos años posteriores a su finalización.

Cláusula 3: Vacaciones
El trabajador tendrá derecho a 30 días naturales de vacaciones anuales.

Cláusula 4: Confidencialidad
Toda información de la empresa será tratada como confidencial.
"""

    # Frases extraídas (simulando salida del LLM)
    extracted_phrases = [
        "Cumplir horario de 9:00 a 18:00",
        "No competir durante vigencia + 2 años",
        "30 días de vacaciones",
        "Esta frase no existe en el documento"
    ]

    # Mapear frases a citas
    citations = map_phrases_to_citations(extracted_phrases, document_text, threshold=0.6)

    # Generar reporte
    report = generate_citation_report(citations)
    print(report)

    print("\n✅ Citation Mapper ready!")
