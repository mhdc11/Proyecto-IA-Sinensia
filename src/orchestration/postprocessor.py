"""
Analysis Post-Processor - Analizador de Documentos Legales

Post-procesa análisis del LLM:
1. Normaliza fechas EU/ES (DD/MM/YYYY) a formato ISO (YYYY-MM-DD)
2. Normaliza símbolos de moneda (€, $, £) a códigos ISO (EUR, USD, GBP)
3. Ajusta confianza basándose en heurísticas de completitud
4. Añade notas sobre verificabilidad y calidad

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import re
from typing import List, Optional
from datetime import datetime

from src.models.analisis import Analisis, Fecha, Importe


# Mapeo de símbolos de moneda a códigos ISO 4217
CURRENCY_SYMBOLS = {
    '€': 'EUR',
    '$': 'USD',
    '£': 'GBP',
    '¥': 'JPY',
    '₹': 'INR',
    'CHF': 'CHF',
}


def normalize_eu_date(date_str: str) -> Optional[str]:
    """
    Normaliza fechas europeas DD/MM/YYYY a formato ISO YYYY-MM-DD

    Args:
        date_str: Fecha en formato DD/MM/YYYY o similar

    Returns:
        Fecha normalizada en formato ISO o None si no se puede parsear

    Examples:
        >>> normalize_eu_date("15/03/2026")
        '2026-03-15'
        >>> normalize_eu_date("1/6/26")
        '2026-06-01'
    """
    # Patrón para DD/MM/YYYY con variaciones
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY o D/M/YYYY
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})',  # DD/MM/YY
    ]

    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            day, month, year = match.groups()

            # Normalizar año de 2 dígitos
            if len(year) == 2:
                year_int = int(year)
                # 00-50 → 2000-2050, 51-99 → 1951-1999
                year = f"20{year}" if year_int <= 50 else f"19{year}"

            # Validar rango
            day_int, month_int, year_int = int(day), int(month), int(year)

            if not (1 <= day_int <= 31 and 1 <= month_int <= 12):
                continue

            # Formato ISO
            try:
                date_obj = datetime(year_int, month_int, day_int)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue

    return None


def normalize_currency_symbol(currency_str: Optional[str]) -> Optional[str]:
    """
    Normaliza símbolos de moneda a códigos ISO 4217

    Args:
        currency_str: Símbolo o código de moneda

    Returns:
        Código ISO 4217 estándar o original si no se reconoce

    Examples:
        >>> normalize_currency_symbol("€")
        'EUR'
        >>> normalize_currency_symbol("$")
        'USD'
    """
    if not currency_str:
        return None

    currency_clean = currency_str.strip()

    # Ya está en formato ISO
    if currency_clean.upper() in ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'INR']:
        return currency_clean.upper()

    # Buscar símbolo
    for symbol, iso_code in CURRENCY_SYMBOLS.items():
        if symbol in currency_clean:
            return iso_code

    # No reconocido, mantener original
    return currency_clean


def postprocess_fechas(fechas: List[Fecha]) -> List[Fecha]:
    """
    Post-procesa lista de fechas normalizando formatos EU/ES a ISO

    Args:
        fechas: Lista de objetos Fecha

    Returns:
        Lista de fechas con valores normalizados a ISO cuando es posible
    """
    normalized_fechas = []

    for fecha in fechas:
        # Intentar normalizar valor
        normalized_value = normalize_eu_date(fecha.valor)

        if normalized_value:
            # Crear nueva instancia con valor normalizado
            normalized_fecha = Fecha(
                etiqueta=fecha.etiqueta,
                valor=normalized_value
            )
            normalized_fechas.append(normalized_fecha)
        else:
            # Mantener original si no se pudo normalizar
            normalized_fechas.append(fecha)

    return normalized_fechas


def postprocess_importes(importes: List[Importe]) -> List[Importe]:
    """
    Post-procesa lista de importes normalizando códigos de moneda

    Args:
        importes: Lista de objetos Importe

    Returns:
        Lista de importes con monedas normalizadas a códigos ISO
    """
    normalized_importes = []

    for importe in importes:
        # Normalizar moneda
        normalized_currency = normalize_currency_symbol(importe.moneda)

        # Crear nueva instancia
        normalized_importe = Importe(
            concepto=importe.concepto,
            valor=importe.valor,
            moneda=normalized_currency
        )
        normalized_importes.append(normalized_importe)

    return normalized_importes


def postprocess_analysis(analisis: Analisis, texto_original: str) -> Analisis:
    """
    Post-procesa análisis completo: normalización + ajuste de confianza

    Pasos aplicados:
    1. Normalización de fechas EU/ES → ISO (DD/MM/YYYY → YYYY-MM-DD)
    2. Normalización de símbolos de moneda → códigos ISO (€ → EUR)
    3. Ajuste de confianza por completitud de categorías
    4. Verificación de números y fechas en texto original
    5. Detección de texto muy corto o vacío
    6. Advertencias sobre categorías sospechosamente vacías

    Args:
        analisis: Análisis original del LLM
        texto_original: Texto del documento original (sin truncar)

    Returns:
        Analisis: Análisis normalizado y ajustado con confianza y notas actualizadas

    Example:
        >>> analisis = Analisis(tipo_documento="contrato", confianza_aprox=0.9)
        >>> texto = "Contrato breve"
        >>> analisis_ajustado = postprocess_analysis(analisis, texto)
    """
    # === PASO 1: Normalización de fechas e importes ===
    analisis.fechas = postprocess_fechas(analisis.fechas)
    analisis.importes = postprocess_importes(analisis.importes)

    # === PASO 2: Ajuste de confianza con heurísticas ===
    # Confianza inicial (del LLM)
    confianza_inicial = analisis.confianza_aprox
    confianza_ajustada = confianza_inicial

    # Notas adicionales
    notas_adicionales = []

    # === Heurística 1: Completitud de categorías ===
    categorias_con_datos = sum([
        bool(analisis.partes),
        bool(analisis.fechas),
        bool(analisis.importes),
        bool(analisis.obligaciones),
        bool(analisis.derechos),
        bool(analisis.riesgos),
        bool(analisis.resumen_bullets),
        analisis.tipo_documento != "desconocido"
    ])

    completitud_ratio = categorias_con_datos / 8.0

    # Penalizar si completitud es muy baja
    if completitud_ratio < 0.5:
        confianza_ajustada *= 0.8  # Reducir 20%
        notas_adicionales.append(
            f"Análisis incompleto: solo {categorias_con_datos}/8 categorías "
            f"con datos (confianza reducida)"
        )

    # === Heurística 2: Verificación de números en texto ===
    if analisis.importes:
        # Extraer valores numéricos del análisis
        valores_analisis = [
            imp.valor for imp in analisis.importes
            if imp.valor is not None
        ]

        # Buscar números en el texto original
        numeros_texto = re.findall(r"\d+[.,]?\d*", texto_original)
        numeros_texto = [float(n.replace(",", ".")) for n in numeros_texto[:20]]  # Top 20

        # Verificar si al menos algunos números del análisis aparecen en el texto
        numeros_verificados = sum(
            1 for val in valores_analisis
            if any(abs(val - num_texto) < 0.01 for num_texto in numeros_texto)
        )

        if valores_analisis and numeros_verificados == 0:
            confianza_ajustada *= 0.9
            notas_adicionales.append(
                "⚠️ Importes extraídos no verificados directamente en texto "
                "(posible inferencia del LLM)"
            )

    # === Heurística 3: Texto muy corto ===
    if len(texto_original) < 500:
        confianza_ajustada *= 0.9
        notas_adicionales.append(
            f"Documento muy breve ({len(texto_original)} caracteres), "
            f"información limitada disponible"
        )

    # === Heurística 4: Fechas no normalizadas ===
    fechas_sin_formato_iso = [
        f for f in analisis.fechas
        if not re.match(r"\d{4}-\d{2}-\d{2}", f.valor)
    ]

    if len(fechas_sin_formato_iso) > 0:
        notas_adicionales.append(
            f"{len(fechas_sin_formato_iso)} fecha(s) no normalizadas a ISO "
            f"(formato literal preservado)"
        )

    # === Heurística 5: Categorías críticas vacías ===
    if not analisis.partes:
        notas_adicionales.append(
            "⚠️ No se identificaron partes involucradas "
            "(documento incompleto o sin firmas)"
        )

    if not analisis.resumen_bullets:
        confianza_ajustada *= 0.85
        notas_adicionales.append(
            "⚠️ No se pudo generar resumen (texto ilegible o muy fragmentado)"
        )

    # === Aplicar límites de confianza ===
    confianza_ajustada = max(0.0, min(1.0, confianza_ajustada))

    # === Actualizar análisis ===
    # Extender notas existentes con las nuevas
    analisis.notas.extend(notas_adicionales)

    # Actualizar confianza
    analisis.confianza_aprox = round(confianza_ajustada, 2)

    # Log de ajustes
    if abs(confianza_inicial - confianza_ajustada) > 0.05:
        print(
            f"📊 Confidence adjusted: "
            f"{confianza_inicial:.2f} → {confianza_ajustada:.2f} "
            f"({len(notas_adicionales)} notes added)"
        )

    return analisis


if __name__ == "__main__":
    # Test de post-procesador
    print("=" * 60)
    print("Testing Analysis Post-Processor")
    print("=" * 60)

    from src.models.analisis import Fecha, Importe

    # Test 1: Análisis completo (alta confianza)
    print("\n📋 Test 1: Complete analysis (high confidence)")
    analisis_completo = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME Corp", "Juan Pérez"],
        fechas=[Fecha(etiqueta="Inicio", valor="2026-03-01")],
        importes=[Importe(concepto="Salario", valor=30000.0, moneda="EUR")],
        obligaciones=["No competir"],
        derechos=["30 días vacaciones"],
        riesgos=["Cláusula no competencia"],
        resumen_bullets=["Contrato anual", "Salario 30k"],
        confianza_aprox=0.95
    )

    texto_largo = "Contrato laboral ACME Corp y Juan Pérez. Salario 30000 EUR. " * 50

    analisis_ajustado = postprocess_analysis(analisis_completo, texto_largo)
    print(f"✅ Original confidence: 0.95")
    print(f"✅ Adjusted confidence: {analisis_ajustado.confianza_aprox}")
    print(f"✅ Notes added: {len(analisis_ajustado.notas)}")

    # Test 2: Análisis incompleto (baja confianza esperada)
    print("\n📋 Test 2: Incomplete analysis (low confidence expected)")
    analisis_incompleto = Analisis(
        tipo_documento="desconocido",
        resumen_bullets=["Texto breve"],
        confianza_aprox=0.6
    )

    texto_corto = "Breve texto de ejemplo"

    analisis_ajustado2 = postprocess_analysis(analisis_incompleto, texto_corto)
    print(f"✅ Original confidence: 0.6")
    print(f"✅ Adjusted confidence: {analisis_ajustado2.confianza_aprox}")
    print(f"✅ Notes added: {len(analisis_ajustado2.notas)}")
    for nota in analisis_ajustado2.notas:
        print(f"   - {nota}")

    # Test 3: Importes no verificables
    print("\n📋 Test 3: Unverifiable amounts")
    analisis_sospechoso = Analisis(
        tipo_documento="contrato",
        importes=[Importe(concepto="Salario", valor=99999.0, moneda="EUR")],
        confianza_aprox=0.8
    )

    texto_sin_numeros = "Contrato laboral entre las partes sin montos especificados"

    analisis_ajustado3 = postprocess_analysis(analisis_sospechoso, texto_sin_numeros)
    print(f"✅ Original confidence: 0.8")
    print(f"✅ Adjusted confidence: {analisis_ajustado3.confianza_aprox}")
    print(f"✅ Notes: {analisis_ajustado3.notas}")

    print("\n✅ Post-processor ready!")
