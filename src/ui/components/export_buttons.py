"""
Export Buttons Component - Analizador de Documentos Legales

Componente de Streamlit para exportar análisis de documentos en formato JSON
con botones de descarga y preservación de caracteres UTF-8.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any

from src.models.dupla import Dupla


def generate_export_filename(documento_nombre: str, timestamp: datetime) -> str:
    """
    Genera nombre de archivo para exportación

    Args:
        documento_nombre: Nombre del documento original
        timestamp: Timestamp de creación de la dupla

    Returns:
        str: Nombre de archivo seguro (sin extensión .json)

    Example:
        >>> generate_export_filename("contrato.pdf", datetime.now())
        'contrato-20260218_143025'
    """
    # Remover extensión del documento original
    nombre_base = documento_nombre.rsplit(".", 1)[0] if "." in documento_nombre else documento_nombre

    # Sanitizar nombre (remover caracteres problemáticos)
    nombre_seguro = "".join(c if c.isalnum() or c in "-_" else "_" for c in nombre_base)

    # Timestamp en formato corto
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

    return f"{nombre_seguro}-{timestamp_str}"


def prepare_export_data(dupla: Dupla) -> Dict[str, Any]:
    """
    Prepara datos de dupla para exportación

    Estructura:
    {
      "documento": {metadata del documento},
      "analisis": {todas las categorías},
      "metadata": {info de exportación}
    }

    Args:
        dupla: Dupla a exportar

    Returns:
        Dict con estructura completa para exportar

    Example:
        >>> data = prepare_export_data(dupla)
        >>> print(data.keys())
        dict_keys(['documento', 'analisis', 'metadata'])
    """
    # Convertir dupla a dict usando Pydantic
    dupla_dict = dupla.model_dump()

    # Estructura de exportación
    export_data = {
        "documento": dupla_dict["documento"],
        "analisis": dupla_dict["analisis"],
        "metadata": {
            "dupla_id": dupla.id,
            "estado": dupla.estado.value,
            "ts_creacion": dupla.ts_creacion.isoformat(),
            "ts_actualizacion": dupla.ts_actualizacion.isoformat(),
            "exported_at": datetime.now().isoformat(),
            "exported_by": "Analizador de Documentos Legales v1.0.0"
        }
    }

    return export_data


def render_export_button(dupla: Dupla, button_label: str = "📥 Exportar JSON") -> None:
    """
    Renderiza botón de exportación con descarga directa

    Args:
        dupla: Dupla a exportar
        button_label: Texto del botón (default: "📥 Exportar JSON")

    Example:
        >>> render_export_button(dupla)
        # Renderiza botón de descarga con JSON generado
    """
    # Preparar datos
    export_data = prepare_export_data(dupla)

    # Generar JSON con formato legible y UTF-8
    json_str = json.dumps(
        export_data,
        indent=2,
        ensure_ascii=False,  # CRÍTICO: Preservar caracteres UTF-8 (ñ, €, etc.)
        default=str  # Convertir objetos no serializables a string
    )

    # Generar nombre de archivo
    filename = generate_export_filename(
        dupla.documento.nombre,
        dupla.ts_creacion
    )

    # Botón de descarga
    st.download_button(
        label=button_label,
        data=json_str.encode('utf-8'),  # CRÍTICO: Codificar en UTF-8
        file_name=f"{filename}.json",
        mime="application/json",
        use_container_width=True,
        help=f"Descargar análisis de '{dupla.documento.nombre}' en formato JSON"
    )


def render_export_all_button(duplas: list, button_label: str = "📥 Exportar Todo el Historial") -> None:
    """
    Renderiza botón para exportar todo el historial como un único archivo

    Args:
        duplas: Lista de duplas a exportar
        button_label: Texto del botón

    Example:
        >>> render_export_all_button(st.session_state['duplas'])
    """
    if not duplas:
        st.info("No hay análisis en el historial para exportar")
        return

    # Preparar datos de todas las duplas
    export_data = {
        "historial": [prepare_export_data(dupla) for dupla in duplas],
        "metadata": {
            "total_documentos": len(duplas),
            "exported_at": datetime.now().isoformat(),
            "exported_by": "Analizador de Documentos Legales v1.0.0"
        }
    }

    # Generar JSON
    json_str = json.dumps(
        export_data,
        indent=2,
        ensure_ascii=False,
        default=str
    )

    # Nombre de archivo con timestamp
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"historial_completo-{timestamp_str}.json"

    # Botón de descarga
    st.download_button(
        label=button_label,
        data=json_str.encode('utf-8'),
        file_name=filename,
        mime="application/json",
        use_container_width=True,
        help=f"Descargar todo el historial ({len(duplas)} documentos) en un único archivo JSON"
    )


def render_export_section(dupla: Dupla, show_export_all: bool = False, all_duplas: list = None) -> None:
    """
    Renderiza sección completa de exportación con opciones

    Args:
        dupla: Dupla actual a exportar
        show_export_all: Si True, muestra también botón de exportar todo
        all_duplas: Lista de todas las duplas (requerido si show_export_all=True)

    Example:
        >>> render_export_section(
        ...     dupla=current_dupla,
        ...     show_export_all=True,
        ...     all_duplas=st.session_state['duplas']
        ... )
    """
    st.markdown("### 📥 Exportación")

    st.caption(
        "Exporta el análisis en formato JSON para uso externo. "
        "Preserva todas las categorías con codificación UTF-8."
    )

    # Botón exportar análisis actual
    col1, col2 = st.columns([2, 1])

    with col1:
        render_export_button(dupla, button_label="📥 Exportar este Análisis")

    with col2:
        # Información del tamaño aproximado
        export_data = prepare_export_data(dupla)
        json_str = json.dumps(export_data, ensure_ascii=False, default=str)
        size_kb = len(json_str.encode('utf-8')) / 1024
        st.metric("Tamaño", f"{size_kb:.1f} KB")

    # Botón exportar todo el historial (opcional)
    if show_export_all and all_duplas:
        st.markdown("---")
        st.markdown("#### Exportar Todo el Historial")

        render_export_all_button(all_duplas)


if __name__ == "__main__":
    # Test del componente
    st.set_page_config(page_title="Export Buttons Test", layout="wide")

    st.title("Export Buttons Component Test")

    # Datos de ejemplo
    from src.models.documento import Documento, TipoFuente
    from src.models.analisis import Analisis, Fecha, Importe
    from src.models.dupla import Dupla, EstadoDupla

    documento = Documento(
        id="test123456789abc",
        nombre="contrato_ejemplo_ñ_€.pdf",
        tipo_fuente=TipoFuente.PDF_NATIVE,
        paginas=5,
        bytes=245760,
        idioma_detectado="es",
        ts_ingesta=datetime.now()
    )

    analisis = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME Corp S.A.", "José María García (DNI: 12345678Z)"],
        fechas=[Fecha(etiqueta="Inicio", valor="2026-03-01")],
        importes=[Importe(concepto="Salario bruto anual", valor=30000.0, moneda="EUR")],
        obligaciones=["No competir durante vigencia + 2 años"],
        derechos=["30 días de vacaciones"],
        riesgos=["Cláusula de no competencia (restrictiva)"],
        resumen_bullets=[
            "Contrato laboral de 1 año",
            "Salario: 30.000 € anuales",
            "30 días de vacaciones"
        ],
        notas=["Caracteres especiales: ñ, á, é, €, ¿, ¡"],
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

    # Test 1: Botón individual
    st.subheader("Test 1: Export Individual")
    render_export_button(dupla)

    st.markdown("---")

    # Test 2: Sección completa
    st.subheader("Test 2: Export Section with All Options")
    render_export_section(
        dupla=dupla,
        show_export_all=True,
        all_duplas=[dupla, dupla]  # Simular 2 duplas
    )

    st.markdown("---")

    # Test 3: Verificar caracteres UTF-8
    st.subheader("Test 3: UTF-8 Character Verification")
    export_data = prepare_export_data(dupla)
    json_preview = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)

    st.code(json_preview[:500], language="json")
    st.caption("✅ Verifica que aparezcan correctamente: ñ, á, é, €, ¿, ¡")
