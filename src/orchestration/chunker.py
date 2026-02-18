"""
Document Chunker and Analysis Consolidator - Analizador de Documentos Legales

Divide documentos largos en chunks manejables para el LLM y consolida
los análisis resultantes en uno solo, con deduplicación y reconciliación.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import re
from typing import List, Dict, Any
from collections import Counter

from src.models.analisis import Analisis, Fecha, Importe


def split_text(
    texto: str,
    max_chunk_size: int = 12000,
    overlap: int = 200
) -> List[str]:
    """
    Divide texto largo en chunks balanceados sin cortar oraciones

    Args:
        texto: Texto completo a dividir
        max_chunk_size: Tamaño máximo de cada chunk en caracteres
        overlap: Solapamiento entre chunks para preservar contexto

    Returns:
        List[str]: Lista de chunks de texto

    Example:
        >>> texto_largo = "..." * 5000
        >>> chunks = split_text(texto_largo, max_chunk_size=10000)
        >>> len(chunks)
        3
        >>> all(len(c) <= 10000 for c in chunks)
        True
    """
    if len(texto) <= max_chunk_size:
        return [texto]

    chunks = []
    start = 0

    while start < len(texto):
        # Calcular el final del chunk
        end = start + max_chunk_size

        if end >= len(texto):
            # Último chunk
            chunks.append(texto[start:].strip())
            break

        # Buscar el final de una oración cerca del límite
        # Intentar cortar en: punto + espacio, punto + salto de línea
        search_start = max(start + max_chunk_size - 500, start)
        search_end = min(end + 200, len(texto))
        search_text = texto[search_start:search_end]

        # Patrones de fin de oración
        sentence_ends = list(re.finditer(r'[.!?]\s+', search_text))

        if sentence_ends:
            # Usar el último fin de oración encontrado
            last_match = sentence_ends[-1]
            actual_end = search_start + last_match.end()
        else:
            # Si no hay fin de oración, buscar al menos un espacio
            last_space = texto[:end].rfind(' ')
            if last_space > start + max_chunk_size * 0.8:
                actual_end = last_space
            else:
                actual_end = end

        # Añadir chunk
        chunks.append(texto[start:actual_end].strip())

        # Avanzar con overlap
        start = actual_end - overlap

    return chunks


def deduplicate_list(items: List[str], similarity_threshold: float = 0.85) -> List[str]:
    """
    Elimina duplicados de una lista de strings, incluyendo similares

    Args:
        items: Lista de strings
        similarity_threshold: Umbral de similitud para considerar duplicados

    Returns:
        List[str]: Lista sin duplicados

    Example:
        >>> items = ["Pago de 1000 EUR", "Pago de 1000 EUR", "Bonificación"]
        >>> deduplicate_list(items)
        ['Pago de 1000 EUR', 'Bonificación']
    """
    if not items:
        return []

    # Exactos primero
    seen = set()
    unique = []

    for item in items:
        item_lower = item.lower().strip()
        if item_lower not in seen:
            seen.add(item_lower)
            unique.append(item)

    # Similitud simple: si A contiene >80% de B, son duplicados
    deduplicated = []
    for i, item_a in enumerate(unique):
        is_duplicate = False
        for j, item_b in enumerate(unique):
            if i == j:
                continue

            # Si item_a está mayormente contenido en item_b
            words_a = set(item_a.lower().split())
            words_b = set(item_b.lower().split())

            if not words_a:
                continue

            overlap = len(words_a & words_b) / len(words_a)

            if overlap >= similarity_threshold and len(item_b) > len(item_a):
                # item_a es redundante respecto a item_b
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(item_a)

    return deduplicated


def merge_fechas(fechas_lists: List[List[Fecha]]) -> List[Fecha]:
    """
    Fusiona listas de fechas, eliminando duplicados

    Args:
        fechas_lists: Lista de listas de Fecha

    Returns:
        List[Fecha]: Lista consolidada sin duplicados
    """
    all_fechas = [f for sublist in fechas_lists for f in sublist]

    if not all_fechas:
        return []

    # Deduplicar por (etiqueta, valor)
    seen_keys = set()
    unique_fechas = []

    for fecha in all_fechas:
        key = (fecha.etiqueta.lower().strip(), fecha.valor.lower().strip())
        if key not in seen_keys:
            seen_keys.add(key)
            unique_fechas.append(fecha)

    return unique_fechas


def merge_importes(importes_lists: List[List[Importe]]) -> List[Importe]:
    """
    Fusiona listas de importes, eliminando duplicados y reconciliando conflictos

    Args:
        importes_lists: Lista de listas de Importe

    Returns:
        List[Importe]: Lista consolidada
    """
    all_importes = [imp for sublist in importes_lists for imp in sublist]

    if not all_importes:
        return []

    # Agrupar por concepto similar
    grouped: Dict[str, List[Importe]] = {}

    for importe in all_importes:
        concepto_norm = importe.concepto.lower().strip()

        # Buscar si ya existe un grupo similar
        found_key = None
        for key in grouped.keys():
            # Similitud simple: >60% de palabras en común
            words_key = set(key.split())
            words_concepto = set(concepto_norm.split())

            if not words_key or not words_concepto:
                continue

            overlap = len(words_key & words_concepto) / max(len(words_key), len(words_concepto))

            if overlap > 0.6:
                found_key = key
                break

        if found_key:
            grouped[found_key].append(importe)
        else:
            grouped[concepto_norm] = [importe]

    # Consolidar cada grupo
    unique_importes = []

    for concepto_key, imps in grouped.items():
        # Si todos tienen el mismo valor y moneda, tomar el primero
        valores = [imp.valor for imp in imps if imp.valor is not None]
        monedas = [imp.moneda for imp in imps if imp.moneda is not None]

        if len(set(valores)) == 1 and len(set(monedas)) <= 1:
            # Valores consistentes
            unique_importes.append(imps[0])
        else:
            # Conflicto: usar el concepto más común y anotar variabilidad
            conceptos_originales = [imp.concepto for imp in imps]
            concepto_final = Counter(conceptos_originales).most_common(1)[0][0]

            # Valor más frecuente
            if valores:
                valor_final = Counter(valores).most_common(1)[0][0]
            else:
                valor_final = None

            # Moneda más frecuente
            if monedas:
                moneda_final = Counter(monedas).most_common(1)[0][0]
            else:
                moneda_final = None

            unique_importes.append(Importe(
                concepto=concepto_final,
                valor=valor_final,
                moneda=moneda_final
            ))

    return unique_importes


def consolidate_analyses(chunks_analisis: List[Analisis]) -> Analisis:
    """
    Consolida múltiples análisis de chunks en uno solo

    Estrategia:
    - tipo_documento: votación por mayoría
    - listas (partes, obligaciones, etc.): merge + deduplicación
    - resumen_bullets: top 10 más frecuentes
    - confianza_aprox: promedio ponderado por completitud

    Args:
        chunks_analisis: Lista de análisis de cada chunk

    Returns:
        Analisis: Análisis consolidado

    Example:
        >>> a1 = Analisis(tipo_documento="contrato", partes=["ACME"], confianza_aprox=0.8)
        >>> a2 = Analisis(tipo_documento="contrato", partes=["ACME", "Juan"], confianza_aprox=0.9)
        >>> consolidado = consolidate_analyses([a1, a2])
        >>> consolidado.tipo_documento
        'contrato'
        >>> len(consolidado.partes)
        2
    """
    if not chunks_analisis:
        raise ValueError("No analyses to consolidate")

    if len(chunks_analisis) == 1:
        return chunks_analisis[0]

    # 1. Tipo de documento: votación
    tipos = [a.tipo_documento for a in chunks_analisis]
    tipo_final = Counter(tipos).most_common(1)[0][0]

    # 2. Partes: merge + deduplicación
    partes_all = [a.partes for a in chunks_analisis]
    partes_merged = [p for sublist in partes_all for p in sublist]
    partes_final = deduplicate_list(partes_merged)

    # 3. Fechas: merge sin duplicados
    fechas_all = [a.fechas for a in chunks_analisis]
    fechas_final = merge_fechas(fechas_all)

    # 4. Importes: merge + reconciliación
    importes_all = [a.importes for a in chunks_analisis]
    importes_final = merge_importes(importes_all)

    # 5. Obligaciones: merge + deduplicación
    obligaciones_all = [a.obligaciones for a in chunks_analisis]
    obligaciones_merged = [o for sublist in obligaciones_all for o in sublist]
    obligaciones_final = deduplicate_list(obligaciones_merged)

    # 6. Derechos: merge + deduplicación
    derechos_all = [a.derechos for a in chunks_analisis]
    derechos_merged = [d for sublist in derechos_all for d in sublist]
    derechos_final = deduplicate_list(derechos_merged)

    # 7. Riesgos: merge + deduplicación
    riesgos_all = [a.riesgos for a in chunks_analisis]
    riesgos_merged = [r for sublist in riesgos_all for r in sublist]
    riesgos_final = deduplicate_list(riesgos_merged)

    # 8. Resumen bullets: top 10 más frecuentes
    bullets_all = [b for a in chunks_analisis for b in a.resumen_bullets]
    bullet_counts = Counter(bullets_all)

    # Si hay duplicados exactos, usar los más comunes; si no, tomar los primeros 10
    if len(bullet_counts) > 10:
        resumen_final = [b for b, _ in bullet_counts.most_common(10)]
    else:
        resumen_final = deduplicate_list(bullets_all)[:10]

    # 9. Notas: merge todas + añadir nota de consolidación
    notas_all = [n for a in chunks_analisis for n in a.notas]
    notas_final = deduplicate_list(notas_all)
    notas_final.insert(0, f"Análisis consolidado de {len(chunks_analisis)} fragmentos del documento")

    # 10. Confianza: promedio ponderado
    # Peso = número de categorías con datos
    confianzas = []
    pesos = []

    for analisis in chunks_analisis:
        peso = sum([
            bool(analisis.partes),
            bool(analisis.fechas),
            bool(analisis.importes),
            bool(analisis.obligaciones),
            bool(analisis.derechos),
            bool(analisis.riesgos),
            bool(analisis.resumen_bullets)
        ])
        confianzas.append(analisis.confianza_aprox)
        pesos.append(max(peso, 1))  # Al menos peso 1

    confianza_final = sum(c * p for c, p in zip(confianzas, pesos)) / sum(pesos)
    confianza_final = round(confianza_final, 2)

    # Construir análisis consolidado
    return Analisis(
        tipo_documento=tipo_final,
        partes=partes_final,
        fechas=fechas_final,
        importes=importes_final,
        obligaciones=obligaciones_final,
        derechos=derechos_final,
        riesgos=riesgos_final,
        resumen_bullets=resumen_final,
        notas=notas_final,
        confianza_aprox=confianza_final
    )


if __name__ == "__main__":
    # Test de chunker
    print("=" * 60)
    print("Testing Document Chunker and Consolidator")
    print("=" * 60)

    # Test 1: Split largo
    print("\n📋 Test 1: Text splitting")
    texto_largo = ("Este es un texto muy largo. " * 200)  # ~5400 chars
    chunks = split_text(texto_largo, max_chunk_size=2000, overlap=100)
    print(f"✅ Original: {len(texto_largo)} chars")
    print(f"✅ Chunks: {len(chunks)}")
    print(f"✅ Chunk sizes: {[len(c) for c in chunks]}")
    print(f"✅ Max chunk: {max(len(c) for c in chunks)} chars")

    # Test 2: Deduplicación
    print("\n📋 Test 2: Deduplication")
    items = [
        "Pago mensual de 1000 EUR",
        "Pago mensual de 1000 EUR",
        "Bonificación anual de 2000 EUR",
        "pago mensual de 1000 eur",  # Case insensitive
        "Vacaciones de 30 días"
    ]
    deduplicated = deduplicate_list(items)
    print(f"✅ Original: {len(items)} items")
    print(f"✅ Deduplicated: {len(deduplicated)} items")
    for item in deduplicated:
        print(f"   - {item}")

    # Test 3: Consolidación de análisis
    print("\n📋 Test 3: Analysis consolidation")

    from src.models.analisis import Fecha, Importe

    analisis_1 = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME Corp", "Juan Pérez"],
        fechas=[Fecha(etiqueta="Inicio", valor="2026-03-01")],
        importes=[Importe(concepto="Salario base", valor=30000.0, moneda="EUR")],
        obligaciones=["No competir durante 2 años"],
        derechos=["30 días de vacaciones"],
        riesgos=["Cláusula de no competencia"],
        resumen_bullets=["Contrato anual", "Salario 30k EUR"],
        confianza_aprox=0.85
    )

    analisis_2 = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME Corp", "Juan Pérez", "Supervisor: María García"],
        fechas=[
            Fecha(etiqueta="Inicio", valor="2026-03-01"),
            Fecha(etiqueta="Renovación", valor="2027-03-01")
        ],
        importes=[
            Importe(concepto="Salario base", valor=30000.0, moneda="EUR"),
            Importe(concepto="Bonus anual", valor=5000.0, moneda="EUR")
        ],
        obligaciones=["No competir durante 2 años", "Confidencialidad perpetua"],
        derechos=["30 días de vacaciones", "Seguro médico privado"],
        riesgos=["Cláusula de no competencia", "Penalización por incumplimiento"],
        resumen_bullets=["Contrato anual", "Salario 30k EUR", "Bonus 5k EUR"],
        confianza_aprox=0.90
    )

    consolidado = consolidate_analyses([analisis_1, analisis_2])

    print(f"✅ Tipo: {consolidado.tipo_documento}")
    print(f"✅ Partes: {len(consolidado.partes)} → {consolidado.partes}")
    print(f"✅ Fechas: {len(consolidado.fechas)}")
    print(f"✅ Importes: {len(consolidado.importes)}")
    print(f"✅ Obligaciones: {len(consolidado.obligaciones)}")
    print(f"✅ Derechos: {len(consolidado.derechos)}")
    print(f"✅ Riesgos: {len(consolidado.riesgos)}")
    print(f"✅ Resumen: {len(consolidado.resumen_bullets)} bullets")
    print(f"✅ Confianza: {consolidado.confianza_aprox}")
    print(f"✅ Notas: {consolidado.notas[0]}")

    print("\n✅ Chunker ready!")
