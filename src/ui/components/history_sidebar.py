"""
History Sidebar Component - Analizador de Documentos Legales

Componente de Streamlit para mostrar historial de duplas en sidebar
con ordenamiento, selección y eliminación.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import streamlit as st
from typing import List, Optional, Callable
from datetime import datetime

from src.models.dupla import Dupla, EstadoDupla
from src.ui.components.export_buttons import render_export_all_button


def get_type_emoji(tipo_documento: str) -> str:
    """
    Retorna emoji apropiado para el tipo de documento

    Args:
        tipo_documento: Tipo de documento (contrato, nomina, etc.)

    Returns:
        str: Emoji representativo
    """
    tipo_map = {
        "contrato": "📄",
        "nomina": "💰",
        "convenio": "📜",
        "certificado": "🏆",
        "poder": "⚖️",
        "anexo": "📎",
        "acta": "📝",
        "desconocido": "❓"
    }

    # Buscar por palabra clave (maneja "contrato_laboral", etc.)
    for keyword, emoji in tipo_map.items():
        if keyword in tipo_documento.lower():
            return emoji

    return "📄"  # Default


def get_estado_badge(estado: EstadoDupla) -> str:
    """
    Retorna badge HTML para el estado de la dupla

    Args:
        estado: Estado de la dupla

    Returns:
        str: HTML badge
    """
    badge_map = {
        EstadoDupla.VALIDO: '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">✓ Válido</span>',
        EstadoDupla.CON_ADVERTENCIAS: '<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">⚠ Advertencias</span>',
        EstadoDupla.INCOMPLETO: '<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">✗ Incompleto</span>'
    }

    return badge_map.get(estado, "")


def sort_duplas(duplas: List[Dupla], order: str) -> List[Dupla]:
    """
    Ordena lista de duplas según criterio

    Args:
        duplas: Lista de duplas a ordenar
        order: Criterio de ordenamiento:
               - "recent": Más reciente primero (default)
               - "oldest": Más antiguo primero
               - "alpha": Alfabético A-Z por nombre

    Returns:
        List[Dupla]: Lista ordenada
    """
    if order == "recent":
        return sorted(duplas, key=lambda d: d.ts_creacion, reverse=True)
    elif order == "oldest":
        return sorted(duplas, key=lambda d: d.ts_creacion, reverse=False)
    elif order == "alpha":
        return sorted(duplas, key=lambda d: d.documento.nombre.lower())
    else:
        # Default: más reciente
        return sorted(duplas, key=lambda d: d.ts_creacion, reverse=True)


def render_history_sidebar(
    duplas: List[Dupla],
    selected_id: Optional[str],
    on_select: Callable[[str], None],
    on_delete: Callable[[str], None],
    on_clear_all: Callable[[], None]
) -> None:
    """
    Renderiza sidebar de historial con ordenamiento, selección y eliminación

    Args:
        duplas: Lista de duplas en el historial
        selected_id: ID de la dupla seleccionada actualmente
        on_select: Callback cuando se selecciona una dupla (recibe ID)
        on_delete: Callback cuando se elimina una dupla (recibe ID)
        on_clear_all: Callback cuando se limpia todo el historial

    Example:
        >>> render_history_sidebar(
        ...     duplas=st.session_state['duplas'],
        ...     selected_id=st.session_state['selected_id'],
        ...     on_select=lambda id: setattr(st.session_state, 'selected_id', id),
        ...     on_delete=lambda id: remove_from_history(id),
        ...     on_clear_all=lambda: clear_history()
        ... )
    """
    st.header("📚 Historial")

    if not duplas:
        st.caption("Los documentos analizados aparecerán aquí")
        return

    # Contador de documentos
    st.caption(f"{len(duplas)} documento(s) analizado(s)")

    # Controles de ordenamiento (T036b)
    if 'sort_order' not in st.session_state:
        st.session_state['sort_order'] = 'recent'

    st.markdown("#### Ordenar por:")
    sort_order = st.radio(
        label="Ordenar por",
        options=["recent", "oldest", "alpha"],
        format_func=lambda x: {
            "recent": "📅 Más reciente",
            "oldest": "📅 Más antiguo",
            "alpha": "🔤 Alfabético A-Z"
        }[x],
        key="history_sort_order",
        label_visibility="collapsed",
        horizontal=False
    )

    # Actualizar orden en session_state
    if sort_order != st.session_state['sort_order']:
        st.session_state['sort_order'] = sort_order

    # Ordenar duplas
    sorted_duplas = sort_duplas(duplas, sort_order)

    st.markdown("---")

    # Lista de duplas con detalles
    for i, dupla in enumerate(sorted_duplas):
        # Contenedor para cada dupla
        with st.container():
            # Emoji por tipo
            tipo_emoji = get_type_emoji(dupla.analisis.tipo_documento)

            # Nombre truncado
            nombre_corto = dupla.documento.nombre
            if len(nombre_corto) > 25:
                nombre_corto = nombre_corto[:22] + "..."

            # Fecha formateada
            fecha_str = dupla.ts_creacion.strftime("%d/%m/%Y %H:%M")

            # Botón de selección
            is_selected = selected_id == dupla.id

            if st.button(
                f"{tipo_emoji} **{nombre_corto}**",
                key=f"select_{dupla.id}_{i}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                on_select(dupla.id)

            # Metadata debajo del botón
            col1, col2 = st.columns([3, 1])

            with col1:
                st.caption(f"📅 {fecha_str}")
                # Badge de estado
                st.markdown(get_estado_badge(dupla.estado), unsafe_allow_html=True)

            with col2:
                # Botón eliminar
                if st.button(
                    "🗑️",
                    key=f"delete_{dupla.id}_{i}",
                    help="Eliminar este análisis",
                    use_container_width=True
                ):
                    # Confirmación
                    st.session_state[f'confirm_delete_{dupla.id}'] = True

            # Modal de confirmación de eliminación
            if st.session_state.get(f'confirm_delete_{dupla.id}', False):
                st.warning(
                    f"⚠️ **¿Eliminar este análisis?**\n\n"
                    f"Documento: `{dupla.documento.nombre}`"
                )

                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button(
                        "✓ Sí, eliminar",
                        key=f"confirm_yes_{dupla.id}_{i}",
                        type="primary",
                        use_container_width=True
                    ):
                        on_delete(dupla.id)
                        st.session_state[f'confirm_delete_{dupla.id}'] = False
                        st.rerun()

                with col_no:
                    if st.button(
                        "✗ Cancelar",
                        key=f"confirm_no_{dupla.id}_{i}",
                        use_container_width=True
                    ):
                        st.session_state[f'confirm_delete_{dupla.id}'] = False
                        st.rerun()

            st.markdown("---")

    # Botón limpiar todo el historial
    st.markdown("#### Acciones")

    # Exportar todo el historial
    render_export_all_button(duplas)

    st.markdown("")  # Espaciado

    if st.button(
        "🗑️ Limpiar Todo el Historial",
        use_container_width=True,
        help="Elimina todos los análisis del historial"
    ):
        st.session_state['confirm_clear_all'] = True

    # Confirmación de limpiar todo
    if st.session_state.get('confirm_clear_all', False):
        st.warning("⚠️ **¿Eliminar TODO el historial?**\n\nEsta acción no se puede deshacer.")

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("✓ Sí, limpiar todo", key="confirm_clear_yes", type="primary"):
                on_clear_all()
                st.session_state['confirm_clear_all'] = False
                st.success("Historial limpiado")
                st.rerun()

        with col_no:
            if st.button("✗ Cancelar", key="confirm_clear_no"):
                st.session_state['confirm_clear_all'] = False
                st.rerun()


if __name__ == "__main__":
    # Test del componente
    st.set_page_config(page_title="History Sidebar Test", layout="wide")

    st.title("History Sidebar Component Test")

    # Datos de ejemplo
    from src.models.documento import Documento, TipoFuente
    from src.models.analisis import Analisis

    # Inicializar session state
    if 'test_duplas' not in st.session_state:
        st.session_state['test_duplas'] = []

        # Crear 3 duplas de ejemplo
        for i in range(3):
            doc = Documento(
                id=f"test{i:016d}",
                nombre=f"documento_ejemplo_{i+1}.pdf",
                tipo_fuente=TipoFuente.PDF_NATIVE,
                paginas=5,
                bytes=100000,
                idioma_detectado="es",
                ts_ingesta=datetime.now()
            )

            analisis = Analisis(
                tipo_documento=["contrato_laboral", "nomina", "convenio"][i],
                confianza_aprox=0.9
            )

            dupla = Dupla(
                id=doc.id,
                documento=doc,
                analisis=analisis,
                ts_creacion=datetime.now(),
                ts_actualizacion=datetime.now(),
                estado=[EstadoDupla.VALIDO, EstadoDupla.CON_ADVERTENCIAS, EstadoDupla.INCOMPLETO][i]
            )

            st.session_state['test_duplas'].append(dupla)

    if 'test_selected_id' not in st.session_state:
        st.session_state['test_selected_id'] = None

    # Callbacks
    def on_select(dupla_id):
        st.session_state['test_selected_id'] = dupla_id

    def on_delete(dupla_id):
        st.session_state['test_duplas'] = [
            d for d in st.session_state['test_duplas'] if d.id != dupla_id
        ]

    def on_clear():
        st.session_state['test_duplas'] = []
        st.session_state['test_selected_id'] = None

    # Renderizar en sidebar
    with st.sidebar:
        render_history_sidebar(
            duplas=st.session_state['test_duplas'],
            selected_id=st.session_state['test_selected_id'],
            on_select=on_select,
            on_delete=on_delete,
            on_clear_all=on_clear
        )

    # Main content
    if st.session_state['test_selected_id']:
        dupla = next(
            (d for d in st.session_state['test_duplas'] if d.id == st.session_state['test_selected_id']),
            None
        )
        if dupla:
            st.success(f"Seleccionado: {dupla.documento.nombre}")
    else:
        st.info("Selecciona un documento del historial")
