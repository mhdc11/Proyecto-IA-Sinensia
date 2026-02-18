"""
Settings Page - Analizador de Documentos Legales

Página de configuración para ajustar parámetros del sistema:
- Modelo LLM (Ollama)
- Temperatura
- Idioma OCR
- Chunking

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import streamlit as st
from typing import Dict, Any

from src.utils.config_loader import get_config, save_user_overrides, reload_config


# Opciones de modelos disponibles
AVAILABLE_MODELS = [
    ("llama3.2:3b", "Llama 3.2 (3B) - Recomendado", "Balance entre calidad y velocidad"),
    ("phi3:mini", "Phi-3 Mini - Ligero", "Rápido, menor precisión (2GB RAM)"),
    ("mistral:7b", "Mistral 7B - Preciso", "Mayor calidad, requiere más recursos (8GB RAM)"),
]

# Opciones de idiomas OCR
OCR_LANGUAGES = [
    ("spa", "Español"),
    ("spa+eng", "Español + Inglés"),
    ("eng", "Inglés"),
]


def render_settings_page():
    """
    Renderiza página de configuración completa con opciones del sistema

    Las configuraciones se guardan en config/user_overrides.yaml
    """
    st.title("⚙️ Configuración")

    st.markdown("""
    Personaliza el comportamiento del sistema. Los cambios se aplicarán al próximo análisis.
    """)

    # Cargar configuración actual
    config = get_config()

    # Contenedor principal con tabs
    tab1, tab2, tab3 = st.tabs(["🤖 Modelo IA", "🔍 OCR", "⚡ Avanzado"])

    # Tab 1: Configuración de Modelo IA
    with tab1:
        st.markdown("### Modelo de Lenguaje (Ollama)")

        st.info(
            "💡 **Nota:** Debes descargar el modelo con `ollama pull <modelo>` antes de usarlo."
        )

        # Selector de modelo
        current_model = config.ollama.model
        model_index = next(
            (i for i, (m, _, _) in enumerate(AVAILABLE_MODELS) if m == current_model),
            0
        )

        selected_model = st.selectbox(
            "Modelo",
            options=range(len(AVAILABLE_MODELS)),
            format_func=lambda i: AVAILABLE_MODELS[i][1],
            index=model_index,
            help="Modelo de IA para analizar documentos"
        )

        model_name, model_label, model_desc = AVAILABLE_MODELS[selected_model]

        st.caption(f"📋 {model_desc}")

        # Mostrar detalles del modelo seleccionado
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Modelo", model_name)

        with col2:
            ram_required = {
                "llama3.2:3b": "4 GB",
                "phi3:mini": "2 GB",
                "mistral:7b": "8 GB"
            }.get(model_name, "Desconocido")
            st.metric("RAM Requerida", ram_required)

        st.markdown("---")

        # Temperatura
        st.markdown("### Temperatura")

        st.markdown("""
        Controla la aleatoriedad de las respuestas:
        - **0.1-0.2**: Determinista, respuestas consistentes (recomendado)
        - **0.3-0.5**: Mayor variabilidad, útil para experimentación
        """)

        temperature = st.slider(
            "Temperatura",
            min_value=0.1,
            max_value=0.5,
            value=config.ollama.temperature,
            step=0.05,
            help="Menor temperatura = respuestas más deterministas"
        )

        # Botón guardar
        if st.button("💾 Guardar Configuración de IA", type="primary", use_container_width=True):
            new_config = {
                "ollama": {
                    "model": model_name,
                    "temperature": float(temperature)
                }
            }

            save_user_overrides(new_config)
            reload_config()  # Recargar config para que se vea inmediatamente
            st.success(f"✅ Configuración guardada: Modelo **{model_name}**, Temperatura **{temperature}**")
            st.info("🔄 Reinicia la aplicación para aplicar los cambios completamente.")

    # Tab 2: Configuración de OCR
    with tab2:
        st.markdown("### Reconocimiento Óptico de Caracteres (OCR)")

        st.markdown("""
        Configuración para procesar documentos escaneados o imágenes.
        """)

        # Idioma OCR
        current_ocr_lang = config.ocr.languages
        ocr_lang_index = next(
            (i for i, (code, _) in enumerate(OCR_LANGUAGES) if code == current_ocr_lang),
            0
        )

        selected_ocr_lang = st.selectbox(
            "Idioma de Reconocimiento",
            options=range(len(OCR_LANGUAGES)),
            format_func=lambda i: OCR_LANGUAGES[i][1],
            index=ocr_lang_index,
            help="Idioma principal del OCR (Tesseract)"
        )

        ocr_lang_code, ocr_lang_name = OCR_LANGUAGES[selected_ocr_lang]

        st.caption(
            f"💡 Asegúrate de tener instalado el paquete de idioma: `tesseract-ocr-{ocr_lang_code.split('+')[0]}`"
        )

        st.markdown("---")

        # DPI (Resolución)
        st.markdown("### Resolución de Escaneo (DPI)")

        dpi = st.radio(
            "Calidad de OCR",
            options=[200, 300, 400, 600],
            index={200: 0, 300: 1, 400: 2, 600: 3}.get(config.ocr.dpi, 1),
            format_func=lambda x: {
                200: "🔹 Rápido (200 DPI)",
                300: "⚡ Balance (300 DPI) - Recomendado",
                400: "🎯 Alta Calidad (400 DPI)",
                600: "💎 Máxima Calidad (600 DPI) - Muy Lento"
            }[x],
            help="Mayor DPI = mejor calidad pero más lento"
        )

        # Estimación de tiempo
        time_estimate = {
            200: "~15-20s por página",
            300: "~30-40s por página",
            400: "~60-80s por página",
            600: "~120-180s por página"
        }[dpi]

        st.caption(f"⏱️ Tiempo estimado: {time_estimate}")

        # Botón guardar
        if st.button("💾 Guardar Configuración de OCR", type="primary", use_container_width=True):
            new_config = {
                "ocr": {
                    "languages": ocr_lang_code,
                    "dpi": dpi
                }
            }

            save_user_overrides(new_config)
            reload_config()  # Recargar config para que se vea inmediatamente
            st.success(f"✅ OCR configurado: Idioma **{ocr_lang_name}**, DPI **{dpi}**")

    # Tab 3: Configuración Avanzada
    with tab3:
        st.markdown("### Opciones Avanzadas")

        # Chunking
        st.markdown("#### Procesamiento de Documentos Largos")

        enable_chunking = st.checkbox(
            "Activar Chunking Automático",
            value=config.chunking.enabled,
            help="Divide documentos largos en partes para análisis. Recomendado mantener activado."
        )

        if enable_chunking:
            chunk_size = st.number_input(
                "Tamaño de Chunk (caracteres)",
                min_value=5000,
                max_value=25000,
                value=15000,
                step=1000,
                help="Documentos mayores a este tamaño se dividirán automáticamente"
            )

            st.caption(f"📄 Documentos > {chunk_size:,} caracteres se procesarán por partes")
        else:
            chunk_size = None
            st.warning("⚠️ Desactivar chunking puede causar errores con documentos largos (>50 páginas)")

        st.markdown("---")

        # Max Tokens
        st.markdown("#### Longitud Máxima de Respuesta")

        max_tokens = st.slider(
            "Max Tokens",
            min_value=1000,
            max_value=8000,
            value=config.ollama.max_tokens,
            step=500,
            help="Longitud máxima de la respuesta del LLM"
        )

        st.caption(
            "💡 Aumentar si los análisis parecen cortados. "
            "Reducir para documentos simples (más rápido)."
        )

        st.markdown("---")

        # Reintentos
        st.markdown("#### Reintentos en Errores")

        max_retries = st.number_input(
            "Reintentos Máximos",
            min_value=1,
            max_value=5,
            value=2,
            help="Intentos ante respuestas JSON inválidas"
        )

        # Botón guardar
        if st.button("💾 Guardar Configuración Avanzada", type="primary", use_container_width=True):
            new_config = {
                "chunking": {
                    "enabled": enable_chunking,
                    "max_chunk_size": chunk_size if enable_chunking else 15000
                },
                "ollama": {
                    "max_tokens": max_tokens,
                    "max_retries": max_retries
                }
            }

            save_user_overrides(new_config)
            reload_config()  # Recargar config para que se vea inmediatamente
            st.success("✅ Configuración avanzada guardada")

    # Sección de información
    st.markdown("---")
    st.markdown("### 📚 Información del Sistema")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Versión", "1.0.0")

    with col2:
        st.metric("Configuración", "config/user_overrides.yaml")

    with col3:
        # Botón restablecer
        if st.button("🔄 Restablecer a Valores por Defecto", help="Elimina personalizaciones"):
            # TODO: Implementar reset
            st.warning("Funcionalidad de reset pendiente")

    st.markdown("---")
    st.caption("💡 Los cambios de configuración se aplican al próximo análisis. "
               "Algunos cambios (modelo, temperatura) pueden requerir reiniciar la aplicación.")


if __name__ == "__main__":
    st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")
    render_settings_page()
