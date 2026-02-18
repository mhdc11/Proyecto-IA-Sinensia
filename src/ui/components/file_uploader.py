"""
File Uploader Component - Analizador de Documentos Legales

Componente de Streamlit para carga segura de archivos con validación de tamaño,
guardado temporal y limpieza automática.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import streamlit as st
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional


# Límites de tamaño
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Tipos de archivo soportados
SUPPORTED_TYPES = ["pdf", "docx", "png", "jpg", "jpeg", "tiff"]


def format_file_size(size_bytes: int) -> str:
    """
    Formatea tamaño de archivo en unidades legibles

    Args:
        size_bytes: Tamaño en bytes

    Returns:
        str: Tamaño formateado (ej: "2.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


def validate_file_size(
    uploaded_file,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES
) -> Tuple[bool, Optional[str]]:
    """
    Valida que el archivo no exceda el tamaño máximo

    Args:
        uploaded_file: Archivo cargado con Streamlit
        max_size_bytes: Tamaño máximo permitido en bytes

    Returns:
        Tuple[bool, Optional[str]]: (es_válido, mensaje_error)

    Example:
        >>> is_valid, error_msg = validate_file_size(uploaded_file)
        >>> if not is_valid:
        ...     st.error(error_msg)
    """
    if uploaded_file.size > max_size_bytes:
        return False, (
            f"❌ **Archivo demasiado grande**: `{uploaded_file.name}` "
            f"({format_file_size(uploaded_file.size)})\n\n"
            f"**Máximo permitido:** {format_file_size(max_size_bytes)}\n\n"
            f"**Sugerencias:**\n"
            f"- Divide el documento en partes más pequeñas\n"
            f"- Comprime el PDF (reduce calidad de imágenes)\n"
            f"- Extrae solo las páginas relevantes"
        )

    return True, None


def save_uploaded_file_temp(uploaded_file) -> Path:
    """
    Guarda archivo cargado en directorio temporal de forma segura

    Args:
        uploaded_file: Archivo cargado con Streamlit

    Returns:
        Path: Ruta al archivo temporal

    Note:
        El archivo temporal NO se elimina automáticamente.
        Usa delete_temp_file() cuando termines de procesarlo.

    Example:
        >>> temp_path = save_uploaded_file_temp(uploaded_file)
        >>> # ... procesar archivo ...
        >>> delete_temp_file(temp_path)
    """
    # Crear directorio temporal si no existe
    temp_dir = Path(tempfile.gettempdir()) / "doc-analyzer"
    temp_dir.mkdir(exist_ok=True)

    # Nombre de archivo seguro (preservar extensión)
    suffix = Path(uploaded_file.name).suffix
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=temp_dir
    )

    # Escribir contenido
    temp_file.write(uploaded_file.getbuffer())
    temp_file.close()

    return Path(temp_file.name)


def delete_temp_file(file_path: Path) -> None:
    """
    Elimina archivo temporal de forma segura

    Args:
        file_path: Ruta al archivo temporal

    Example:
        >>> delete_temp_file(temp_path)
    """
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        # Silent fail - temp files se limpian periódicamente por el SO
        pass


def render_file_uploader() -> List[Tuple[str, Path]]:
    """
    Renderiza componente de carga de archivos con validación

    Returns:
        List[Tuple[str, Path]]: Lista de tuplas (nombre_archivo, ruta_temporal)
                                 Solo archivos válidos (dentro del límite de tamaño)

    Example:
        >>> valid_files = render_file_uploader()
        >>> for name, temp_path in valid_files:
        ...     process_document(temp_path)
        ...     delete_temp_file(temp_path)
    """
    st.subheader("📂 Cargar Documentos")

    uploaded_files = st.file_uploader(
        label="Selecciona uno o varios archivos",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        help=f"Formatos: {', '.join(SUPPORTED_TYPES).upper()} | Tamaño máx: {MAX_FILE_SIZE_MB} MB por archivo",
        key="file_uploader_main"
    )

    # Si no hay archivos, retornar lista vacía
    if not uploaded_files:
        st.info(
            f"💡 **Tip:** Puedes cargar múltiples archivos a la vez. "
            f"Máximo {MAX_FILE_SIZE_MB} MB por archivo."
        )
        return []

    # Validar y procesar cada archivo
    valid_files = []
    invalid_count = 0

    for uploaded_file in uploaded_files:
        # Validar tamaño
        is_valid, error_msg = validate_file_size(uploaded_file)

        if not is_valid:
            # Mostrar error específico
            st.error(error_msg)
            invalid_count += 1
            continue

        # Guardar temporalmente
        try:
            temp_path = save_uploaded_file_temp(uploaded_file)
            valid_files.append((uploaded_file.name, temp_path))
        except Exception as e:
            st.error(
                f"❌ **Error guardando archivo:** `{uploaded_file.name}`\n\n"
                f"```\n{str(e)}\n```"
            )
            invalid_count += 1
            continue

    # Mostrar resumen de archivos cargados
    if valid_files:
        st.success(
            f"✅ **{len(valid_files)} archivo(s) cargado(s) correctamente**"
        )

        # Listar archivos con tamaños
        with st.expander(f"📄 Ver lista de archivos ({len(valid_files)})", expanded=False):
            for name, temp_path in valid_files:
                file_size = temp_path.stat().st_size
                st.text(f"• {name} - {format_file_size(file_size)}")

    if invalid_count > 0:
        st.warning(
            f"⚠️ {invalid_count} archivo(s) rechazado(s) por exceder {MAX_FILE_SIZE_MB} MB"
        )

    return valid_files


if __name__ == "__main__":
    # Test del componente (requiere ejecutar con Streamlit)
    st.set_page_config(page_title="File Uploader Test", layout="wide")

    st.title("File Uploader Component Test")

    valid_files = render_file_uploader()

    if valid_files:
        st.markdown("---")
        st.subheader("Archivos Válidos:")

        for name, temp_path in valid_files:
            st.write(f"**{name}**")
            st.code(str(temp_path))

            # Botón para limpiar
            if st.button(f"🗑️ Eliminar temp: {name}", key=f"delete_{name}"):
                delete_temp_file(temp_path)
                st.success(f"Eliminado: {temp_path}")
                st.rerun()
