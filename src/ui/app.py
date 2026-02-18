"""
Main Streamlit Application - Analizador de Documentos Legales

Aplicación web local para análisis de documentos legales, laborales y administrativos
con IA local (Ollama) y procesamiento 100% privado.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import streamlit as st
import threading
from pathlib import Path
from typing import List, Dict

from src.models.dupla import Dupla
from src.orchestration.analyzer import analyze_document, AnalysisError, CancelledException
from src.orchestration.ollama_client import OllamaClient
from src.ui.components.file_uploader import render_file_uploader, delete_temp_file
from src.ui.components.analysis_view import render_analysis_view
from src.ui.components.history_sidebar import render_history_sidebar
from src.utils.config_loader import get_config
from src.utils.language_detector import detect_language
from src.persistence.json_store import load_history, add_to_history, remove_from_history, clear_history

# Page configuration (DEBE SER LA PRIMERA LLAMADA de Streamlit)
st.set_page_config(
    page_title="Analizador de Documentos Legales",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/doc-analyzer',
        'Report a bug': 'https://github.com/yourusername/doc-analyzer/issues',
        'About': """
        ## Analizador de Documentos Legales

        Herramienta local para analizar documentos legales, laborales y administrativos
        usando IA local (Ollama) con privacidad garantizada.

        **Características:**
        - 100% local y privado
        - Soporte para PDF, DOCX, imágenes
        - OCR integrado para documentos escaneados
        - Análisis estructurado en 8 categorías
        - Historial de análisis navegable

        **Versión:** 1.0.0
        """
    }
)


def init_session_state():
    """
    Inicializa estado de sesión de Streamlit

    Estado mantenido:
    - duplas: Lista de duplas (documento ↔ análisis)
    - selected_id: ID de la dupla seleccionada actualmente
    - processing: Flag de procesamiento en curso
    - cancel_token: threading.Event para cancelación
    - sort_order: Orden del historial (recent/oldest/alpha)
    """
    if 'duplas' not in st.session_state:
        # Cargar historial desde disco al iniciar
        st.session_state['duplas'] = load_history()

    if 'selected_id' not in st.session_state:
        st.session_state['selected_id'] = None

    if 'processing' not in st.session_state:
        st.session_state['processing'] = False

    if 'cancel_token' not in st.session_state:
        st.session_state['cancel_token'] = threading.Event()

    if 'sort_order' not in st.session_state:
        st.session_state['sort_order'] = 'recent'


def check_ollama_health() -> bool:
    """
    Verifica si Ollama está disponible

    Returns:
        bool: True si Ollama responde, False si no
    """
    try:
        client = OllamaClient()
        return client.is_healthy()
    except Exception:
        return False


def render_sidebar():
    """
    Renderiza sidebar con configuración e historial
    """
    with st.sidebar:
        st.header("⚙️ Configuración")

        # Verificación de Ollama
        st.markdown("### Estado del Sistema")

        if check_ollama_health():
            st.success("✅ Ollama: Conectado")
            config = get_config()
            st.info(f"📦 Modelo: `{config.ollama.model}`")
            st.caption(f"Temperatura: {config.ollama.temperature}")
        else:
            st.error("❌ Ollama: Desconectado")
            st.warning(
                "**Ollama no está corriendo.**\n\n"
                "Inicia Ollama con:\n"
                "```\nollama serve\n```"
            )

        st.markdown("---")

        # Historial mejorado con componente
        def on_select(dupla_id: str):
            st.session_state['selected_id'] = dupla_id
            st.rerun()

        def on_delete(dupla_id: str):
            remove_from_history(dupla_id)
            st.session_state['duplas'] = load_history()
            if st.session_state['selected_id'] == dupla_id:
                st.session_state['selected_id'] = None
            st.rerun()

        def on_clear_all():
            clear_history()
            st.session_state['duplas'] = []
            st.session_state['selected_id'] = None
            st.rerun()

        render_history_sidebar(
            duplas=st.session_state['duplas'],
            selected_id=st.session_state['selected_id'],
            on_select=on_select,
            on_delete=on_delete,
            on_clear_all=on_clear_all
        )

        st.markdown("---")

        # Importar historial desde JSON
        st.markdown("#### Importar Historial")
        uploaded_file = st.file_uploader(
            "Cargar historial desde JSON",
            type=['json'],
            help="Importa un archivo de historial exportado previamente. "
                 "Las duplas se fusionarán con el historial actual.",
            key="import_history_uploader"
        )

        if uploaded_file is not None:
            try:
                import json
                from io import StringIO

                # Leer contenido del archivo
                content = uploaded_file.read().decode('utf-8')
                data = json.loads(content)

                # Determinar formato: historial completo o análisis individual
                if 'historial' in data:
                    # Formato de exportación completa
                    duplas_to_import = data['historial']
                    count = len(duplas_to_import)
                elif 'documento' in data and 'analisis' in data:
                    # Formato de análisis individual
                    duplas_to_import = [data]
                    count = 1
                else:
                    st.error("❌ **Formato de archivo inválido**\\n\\nEl archivo no tiene el formato esperado.")
                    duplas_to_import = []
                    count = 0

                if count > 0:
                    # Confirmar importación
                    st.info(f"📊 **{count} análisis encontrado(s) en el archivo**")

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "✓ Importar",
                            key="confirm_import",
                            type="primary",
                            use_container_width=True
                        ):
                            # Importar cada dupla
                            success_count = 0
                            error_count = 0

                            for dupla_data in duplas_to_import:
                                try:
                                    # Reconstruir objetos Pydantic
                                    dupla = Dupla(**dupla_data)

                                    # Añadir al historial con política "replace"
                                    add_to_history(dupla, policy="replace")
                                    success_count += 1

                                except Exception as e:
                                    error_count += 1
                                    continue

                            # Recargar historial desde disco
                            st.session_state['duplas'] = load_history()

                            # Mensaje de resultado
                            if error_count == 0:
                                st.success(f"✅ **Importación exitosa:** {success_count} análisis importado(s)")
                            else:
                                st.warning(
                                    f"⚠️ **Importación parcial:**\\n\\n"
                                    f"- ✅ Exitosos: {success_count}\\n"
                                    f"- ❌ Fallidos: {error_count}"
                                )

                            st.rerun()

                    with col2:
                        if st.button(
                            "✗ Cancelar",
                            key="cancel_import",
                            use_container_width=True
                        ):
                            st.rerun()

            except json.JSONDecodeError:
                st.error(
                    "❌ **Error de formato**\\n\\n"
                    "El archivo no contiene JSON válido. "
                    "Asegúrate de cargar un archivo exportado desde esta aplicación."
                )
            except Exception as e:
                st.error(f"❌ **Error inesperado:**\\n\\n```\\n{str(e)}\\n```")

        st.markdown("---")

        # Footer
        st.caption("🔒 Privacidad garantizada - Todo el procesamiento es local")
        st.caption(f"Versión 1.0.0")


def process_documents(valid_files: List[tuple]) -> None:
    """
    Procesa documentos cargados con indicadores de progreso

    Args:
        valid_files: Lista de tuplas (nombre_archivo, ruta_temporal)
    """
    if not valid_files:
        return

    # Verificar Ollama
    if not check_ollama_health():
        st.error(
            "❌ **Ollama no está disponible**\n\n"
            "Por favor, inicia Ollama con: `ollama serve`"
        )
        return

    # Botón de procesamiento
    if st.button(f"🚀 Analizar {len(valid_files)} documento(s)", type="primary", use_container_width=True):
        st.session_state['processing'] = True
        st.session_state['cancel_token'] = threading.Event()

        # Progress bar general
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Procesar cada archivo
        for i, (filename, temp_path) in enumerate(valid_files):
            try:
                # Actualizar progress
                progress_pct = i / len(valid_files)
                progress_bar.progress(progress_pct)
                status_text.markdown(f"📄 **Procesando:** `{filename}` ({i+1}/{len(valid_files)})")

                # Spinners por etapa
                with st.spinner(f"⏳ Extrayendo texto de {filename}..."):
                    # TODO: Podríamos mostrar sub-etapas aquí si fuera necesario
                    pass

                with st.spinner(f"🤖 Analizando con IA local..."):
                    documento, analisis, dupla, documento_text = analyze_document(
                        file_path=temp_path,
                        cancellation_token=st.session_state['cancel_token']
                    )

                # Detectar idioma
                with st.spinner("🌐 Detectando idioma..."):
                    if dupla.analisis.resumen_bullets:
                        texto_muestra = " ".join(dupla.analisis.resumen_bullets)
                        idioma = detect_language(texto_muestra)
                        dupla.documento.idioma_detectado = idioma

                # Guardar en historial (persistente con política "replace")
                add_to_history(dupla, policy="replace")

                # Actualizar session state desde disco
                st.session_state['duplas'] = load_history()
                st.session_state['selected_id'] = dupla.id

                # Guardar texto del documento para citation mapping (solo para este documento recién analizado)
                if 'document_texts' not in st.session_state:
                    st.session_state['document_texts'] = {}
                st.session_state['document_texts'][dupla.id] = documento_text

                # Limpieza del archivo temporal
                delete_temp_file(temp_path)

                # Success mensaje
                st.success(f"✅ **{filename}** analizado correctamente")

            except CancelledException:
                status_text.info("⏹ **Análisis cancelado por el usuario**")
                break

            except AnalysisError as e:
                st.error(f"❌ **Error analizando {filename}:**\n\n```\n{str(e)}\n```")
                # Limpieza del archivo temporal
                delete_temp_file(temp_path)
                continue

            except Exception as e:
                st.error(f"❌ **Error inesperado con {filename}:**\n\n```\n{str(e)}\n```")
                delete_temp_file(temp_path)
                continue

        # Finalizar
        progress_bar.progress(1.0)
        status_text.success(f"✅ **Procesamiento completado:** {len(valid_files)} documento(s)")
        st.session_state['processing'] = False

        st.rerun()


def render_analysis_section():
    """
    Renderiza sección de análisis (vista del documento seleccionado)
    """
    if not st.session_state['selected_id']:
        st.info("👈 Selecciona un documento del historial para ver su análisis")
        return

    # Buscar dupla seleccionada
    dupla = next(
        (d for d in st.session_state['duplas'] if d.id == st.session_state['selected_id']),
        None
    )

    if not dupla:
        st.warning("⚠️ Documento no encontrado en el historial")
        return

    # Obtener texto del documento si está disponible (solo documentos recién analizados)
    documento_text = None
    if 'document_texts' in st.session_state and dupla.id in st.session_state['document_texts']:
        documento_text = st.session_state['document_texts'][dupla.id]

    # Renderizar vista de análisis
    render_analysis_view(dupla.documento, dupla.analisis, dupla, documento_text=documento_text)


def main():
    """
    Punto de entrada principal de la aplicación
    """
    # Inicializar estado
    init_session_state()

    # Sidebar
    render_sidebar()

    # Header principal
    st.title("📄 Analizador de Documentos Legales")
    st.markdown(
        """
        <div style="padding: 1rem; background-color: #f0f2f6; border-radius: 0.5rem; margin-bottom: 2rem;">
        <p style="margin: 0; color: #31333F;">
        🔒 <strong>Procesamiento 100% Local</strong> - Tus documentos nunca salen de tu equipo.
        Usa <strong>Ollama</strong> (IA local) para extraer puntos clave de contratos, nóminas, convenios y más.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Instrucciones rápidas
    with st.expander("ℹ️ Cómo usar esta aplicación", expanded=False):
        st.markdown(
            """
            ### Pasos:
            1. **Carga uno o varios documentos** usando el botón de arriba
            2. **Haz clic en "Analizar"** - el sistema extraerá texto (con OCR si es necesario)
            3. **Revisa los resultados** organizados en categorías:
               - Partes involucradas
               - Fechas relevantes
               - Importes y datos económicos
               - Obligaciones y deberes
               - Derechos y beneficios
               - Riesgos y alertas
               - Resumen en bullets
            4. **Navega tu historial** desde la barra lateral
            5. **Exporta resultados** en formato JSON (próximamente)

            ### Formatos soportados:
            - 📄 PDF (nativo y escaneado con OCR)
            - 📝 DOCX
            - 🖼️ Imágenes (PNG, JPG, TIFF con OCR)

            ### Requisitos:
            - **Ollama** corriendo en `localhost:11434`
            - Modelo instalado: `llama3.2:3b` (o configurado en `config/ollama_config.yaml`)
            - **Tesseract OCR** instalado (para documentos escaneados)
            """
        )

    st.markdown("---")

    # Sección de carga y procesamiento
    if not st.session_state['selected_id']:
        # File uploader
        valid_files = render_file_uploader()

        # Procesar documentos
        if valid_files:
            process_documents(valid_files)

    # Sección de análisis (si hay documento seleccionado)
    else:
        # Botón para volver a cargar
        if st.button("⬅️ Volver a cargar documentos"):
            st.session_state['selected_id'] = None
            st.rerun()

        st.markdown("---")

        # Renderizar análisis
        render_analysis_section()


if __name__ == "__main__":
    main()
