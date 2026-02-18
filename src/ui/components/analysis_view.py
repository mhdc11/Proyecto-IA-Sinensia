"""
Analysis View Component - Analizador de Documentos Legales

Componente de Streamlit para visualizar análisis de documentos
en formato de tarjetas/bullets organizadas por categorías.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import streamlit as st
from datetime import datetime
from typing import Optional, List

from src.models.analisis import Analisis
from src.models.documento import Documento
from src.models.dupla import Dupla, EstadoDupla
from src.ui.components.export_buttons import render_export_section
from src.orchestration.citation_mapper import map_phrases_to_citations


def render_metadata_section(documento: Documento, dupla: Dupla) -> None:
    """
    Renderiza sección de metadatos del documento

    Args:
        documento: Objeto Documento con metadatos
        dupla: Objeto Dupla con estado y timestamps
    """
    st.markdown("### 📊 Información del Documento")

    # 4 columnas para métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Páginas",
            value=documento.paginas or "—",
            help="Número de páginas del documento"
        )

    with col2:
        st.metric(
            label="Tipo Fuente",
            value=documento.tipo_fuente.value.replace("_", " ").title(),
            help="Tipo de extracción: PDF nativo, PDF con OCR, DOCX, o imagen"
        )

    with col3:
        tamaño_kb = documento.bytes / 1024 if documento.bytes else 0
        tamaño_str = f"{tamaño_kb:.1f} KB" if tamaño_kb < 1024 else f"{tamaño_kb/1024:.1f} MB"
        st.metric(
            label="Tamaño",
            value=tamaño_str,
            help="Tamaño del archivo original"
        )

    with col4:
        # Estado de la dupla con color
        estado_emoji = {
            EstadoDupla.VALIDO: "✅",
            EstadoDupla.CON_ADVERTENCIAS: "⚠️",
            EstadoDupla.INCOMPLETO: "❌"
        }

        st.metric(
            label="Estado",
            value=f"{estado_emoji.get(dupla.estado, '❓')} {dupla.estado.value.replace('_', ' ').title()}",
            help="Estado del análisis: válido, con advertencias, o incompleto"
        )

    # Timestamps
    st.caption(
        f"📅 Analizado: {dupla.ts_creacion.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Idioma: {documento.idioma_detectado or 'No detectado'}"
    )


def render_category_section(
    title: str,
    icon: str,
    items: list,
    empty_message: str = "No disponible",
    is_structured: bool = False
) -> None:
    """
    Renderiza una sección de categoría con expander

    Args:
        title: Título de la categoría
        icon: Emoji o icono para la categoría
        items: Lista de items a mostrar
        empty_message: Mensaje si la lista está vacía
        is_structured: Si True, items son objetos (Fecha, Importe); si False, strings
    """
    with st.expander(f"{icon} **{title}** ({len(items)})", expanded=len(items) > 0):
        if not items:
            st.info(f"ℹ️ {empty_message}")
            return

        if is_structured:
            # Items estructurados (Fecha, Importe)
            for item in items:
                if hasattr(item, "etiqueta"):  # Fecha
                    st.markdown(f"- **{item.etiqueta}:** `{item.valor}`")
                elif hasattr(item, "concepto"):  # Importe
                    valor_str = f"{item.valor:,.2f}" if item.valor is not None else "No especificado"
                    moneda_str = item.moneda or ""
                    st.markdown(f"- **{item.concepto}:** `{valor_str} {moneda_str}`")
                else:
                    st.markdown(f"- {item}")
        else:
            # Items simples (strings)
            for item in items:
                st.markdown(f"- {item}")


def render_category_with_citations(
    title: str,
    icon: str,
    items: List[str],
    documento_text: str,
    empty_message: str = "No disponible"
) -> None:
    """
    Renderiza una sección de categoría con referencias al documento original

    Args:
        title: Título de la categoría
        icon: Emoji o icono para la categoría
        items: Lista de frases/items a mostrar
        documento_text: Texto completo del documento para buscar citas
        empty_message: Mensaje si la lista está vacía
    """
    with st.expander(f"{icon} **{title}** ({len(items)})", expanded=len(items) > 0):
        if not items:
            st.info(f"ℹ️ {empty_message}")
            return

        # Mapear frases a citas (solo una vez para todas)
        citations_map = map_phrases_to_citations(items, documento_text, threshold=0.6)

        for item in items:
            citation = citations_map.get(item)

            if citation:
                # Item con cita encontrada
                st.markdown(f"- {item}")

                # Mostrar ubicación en un expander compacto
                with st.expander(f"📍 Ver ubicación (líneas {citation.start_line}-{citation.end_line}, similitud: {citation.similarity:.0%})", expanded=False):
                    st.caption(f"**Contexto del documento:**")
                    st.code(citation.snippet, language="text")
            else:
                # Item sin cita (no encontrado)
                st.markdown(f"- {item}")
                st.caption("   ⚠️ _No se encontró ubicación exacta en el documento_")


def render_analysis_view(
    documento: Documento,
    analisis: Analisis,
    dupla: Dupla,
    documento_text: Optional[str] = None
) -> None:
    """
    Renderiza vista completa de análisis con todas las categorías

    Args:
        documento: Objeto Documento
        analisis: Objeto Analisis con categorías
        dupla: Objeto Dupla con estado

    Example:
        >>> render_analysis_view(documento, analisis, dupla)
    """
    # Header con nombre del documento
    st.header(f"📄 {documento.nombre}")

    # Mostrar advertencias si existen
    if dupla.estado == EstadoDupla.CON_ADVERTENCIAS:
        st.warning(
            "⚠️ **Análisis con advertencias** - Algunas categorías pueden estar incompletas o tener baja confianza. "
            "Revisa las notas al final para más detalles."
        )
    elif dupla.estado == EstadoDupla.INCOMPLETO:
        st.error(
            "❌ **Análisis incompleto** - El documento no pudo analizarse correctamente. "
            "Puede ser muy corto, ilegible, o de un formato no soportado."
        )

    # Sección de metadatos
    render_metadata_section(documento, dupla)

    st.markdown("---")

    # Tipo de documento (destacado)
    st.markdown("### 📑 Clasificación")
    tipo_display = analisis.tipo_documento.replace("_", " ").title()

    if analisis.tipo_documento != "desconocido":
        st.success(f"**Tipo:** {tipo_display}")
    else:
        st.warning(f"**Tipo:** {tipo_display}")

    st.caption(f"Confianza: {analisis.confianza_aprox * 100:.0f}%")

    st.markdown("---")

    # Sección de categorías (2 columnas)
    col_left, col_right = st.columns(2)

    with col_left:
        # Partes
        render_category_section(
            title="Partes Involucradas",
            icon="👥",
            items=analisis.partes,
            empty_message="No se identificaron partes en el documento"
        )

        # Obligaciones (con citas si disponible)
        if documento_text:
            render_category_with_citations(
                title="Obligaciones",
                icon="📋",
                items=analisis.obligaciones,
                documento_text=documento_text,
                empty_message="No se identificaron obligaciones"
            )
        else:
            render_category_section(
                title="Obligaciones",
                icon="📋",
                items=analisis.obligaciones,
                empty_message="No se identificaron obligaciones"
            )

        # Riesgos (con citas si disponible)
        if documento_text:
            render_category_with_citations(
                title="Riesgos y Alertas",
                icon="⚠️",
                items=analisis.riesgos,
                documento_text=documento_text,
                empty_message="No se identificaron riesgos o cláusulas sensibles"
            )
        else:
            render_category_section(
                title="Riesgos y Alertas",
                icon="⚠️",
                items=analisis.riesgos,
                empty_message="No se identificaron riesgos o cláusulas sensibles"
            )

    with col_right:
        # Fechas
        render_category_section(
            title="Fechas Relevantes",
            icon="📅",
            items=analisis.fechas,
            empty_message="No se identificaron fechas",
            is_structured=True
        )

        # Derechos (con citas si disponible)
        if documento_text:
            render_category_with_citations(
                title="Derechos",
                icon="✅",
                items=analisis.derechos,
                documento_text=documento_text,
                empty_message="No se identificaron derechos"
            )
        else:
            render_category_section(
                title="Derechos",
                icon="✅",
                items=analisis.derechos,
                empty_message="No se identificaron derechos"
            )

        # Importes
        render_category_section(
            title="Importes y Datos Económicos",
            icon="💰",
            items=analisis.importes,
            empty_message="No se identificaron importes",
            is_structured=True
        )

    # Resumen (ancho completo)
    st.markdown("---")
    render_category_section(
        title="Resumen Ejecutivo",
        icon="📝",
        items=analisis.resumen_bullets,
        empty_message="No se generó resumen"
    )

    # Notas (si existen)
    if analisis.notas:
        st.markdown("---")
        render_category_section(
            title="Notas y Observaciones",
            icon="📌",
            items=analisis.notas,
            empty_message="Sin notas adicionales"
        )

    # Sección de exportación
    st.markdown("---")
    render_export_section(
        dupla=dupla,
        show_export_all=False,  # No mostramos exportar todo desde vista individual
        all_duplas=None
    )


if __name__ == "__main__":
    # Test del componente con datos de ejemplo
    st.set_page_config(page_title="Analysis View Test", layout="wide")

    st.title("Analysis View Component Test")

    # Datos de ejemplo
    from src.models.analisis import Fecha, Importe

    documento = Documento(
        id="abc123456789abcd",
        nombre="contrato_ejemplo.pdf",
        tipo_fuente="pdf_native",
        paginas=5,
        bytes=245760,
        idioma_detectado="es",
        ts_ingesta=datetime.now()
    )

    analisis = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME Corp S.A. (CIF: A12345678)", "Juan Pérez García (DNI: 12345678Z)"],
        fechas=[
            Fecha(etiqueta="Inicio", valor="2026-03-01"),
            Fecha(etiqueta="Fin", valor="2027-02-28"),
            Fecha(etiqueta="Periodo de prueba", valor="3 meses")
        ],
        importes=[
            Importe(concepto="Salario bruto anual", valor=30000.0, moneda="EUR"),
            Importe(concepto="Bonus anual", valor=5000.0, moneda="EUR")
        ],
        obligaciones=[
            "No competir durante la vigencia del contrato + 2 años post-finalización",
            "Mantener confidencialidad sobre información de la empresa",
            "Cumplir horario de 9:00 a 18:00 de lunes a viernes"
        ],
        derechos=[
            "30 días naturales de vacaciones anuales",
            "Seguro médico privado",
            "Bonus por objetivos hasta 5.000 EUR anuales"
        ],
        riesgos=[
            "Cláusula de no competencia de 2 años (restrictiva)",
            "Penalización por incumplimiento de confidencialidad: 10.000 EUR"
        ],
        resumen_bullets=[
            "Contrato laboral de 1 año renovable",
            "Salario: 30.000 EUR + bonus hasta 5.000 EUR",
            "Periodo de prueba: 3 meses",
            "No competencia: 2 años post-finalización",
            "30 días de vacaciones + seguro médico"
        ],
        notas=[
            "Documento con buena calidad de escaneo",
            "Todas las categorías identificadas correctamente"
        ],
        confianza_aprox=0.92
    )

    dupla = Dupla(
        id=documento.id,
        documento=documento,
        analisis=analisis,
        ts_creacion=datetime.now(),
        ts_actualizacion=datetime.now(),
        estado=EstadoDupla.VALIDO
    )

    # Renderizar vista
    render_analysis_view(documento, analisis, dupla)
