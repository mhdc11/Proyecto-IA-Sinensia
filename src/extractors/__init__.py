"""
Extractors Package - Analizador de Documentos Legales

Módulo de orquestación que coordina todos los extractores de texto.
Proporciona extracción automática con fallback inteligente (PDF nativo → OCR).

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from pathlib import Path
from typing import Tuple, Optional

from src.extractors.base import detect_source, is_supported_format
from src.extractors.pdf_native import extract_text_pdf_native, has_extractable_text
from src.extractors.pdf_ocr import extract_text_pdf_ocr
from src.extractors.docx_extractor import extract_text_docx
from src.extractors.image_extractor import extract_text_image
from src.models.documento import TipoFuente


def extract_text_auto(
    file_path: Path,
    ocr_dpi: int = 300,
    ocr_lang: str = "spa",
    force_ocr: bool = False,
) -> Tuple[str, Optional[int], str]:
    """
    Extrae texto automáticamente detectando el tipo de documento y aplicando
    el extractor apropiado con fallback inteligente.

    Estrategia:
    1. Detectar tipo de archivo (PDF, DOCX, imagen, etc.)
    2. Para PDF: intentar extracción nativa primero
       - Si falla o no hay texto → fallback automático a OCR
    3. Para otros formatos: aplicar extractor correspondiente

    Args:
        file_path: Ruta al archivo a procesar
        ocr_dpi: DPI para OCR (default: 300)
        ocr_lang: Idioma(s) para OCR (default: 'spa')
        force_ocr: Si True, fuerza OCR incluso para PDFs con texto (útil para debugging)

    Returns:
        Tuple[str, Optional[int], str]: (texto, num_paginas, tipo_fuente_final)
            - texto: Texto extraído
            - num_paginas: Número de páginas (None para imágenes/TXT)
            - tipo_fuente_final: Tipo de fuente real usado ("pdf_native", "pdf_ocr", etc.)

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el formato no es soportado
        RuntimeError: Si todos los métodos de extracción fallan

    Example:
        >>> from pathlib import Path
        >>> texto, paginas, tipo = extract_text_auto(Path("contrato.pdf"))
        >>> print(f"Extracted {len(texto)} chars from {paginas} pages using {tipo}")
        Extracted 15620 chars from 12 pages using pdf_native
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not is_supported_format(file_path):
        raise ValueError(
            f"Unsupported file format: {file_path.suffix}. "
            f"Supported formats: PDF, DOCX, PNG, JPG, TIFF, TXT"
        )

    # Detectar tipo de fuente inicial
    tipo_fuente = detect_source(file_path)
    print(f"🔍 Detected source type: {tipo_fuente}")

    # ==== ESTRATEGIA POR TIPO DE ARCHIVO ====

    # PDF: Intenta nativo primero, fallback a OCR si falla
    if tipo_fuente == TipoFuente.PDF_NATIVE.value:
        if not force_ocr:
            try:
                print("🔄 Attempting native PDF extraction...")
                texto, paginas = extract_text_pdf_native(file_path)
                print(f"✅ Native PDF extraction successful: {len(texto)} characters")
                return texto, paginas, TipoFuente.PDF_NATIVE.value
            except RuntimeError as e:
                # Si falla nativo (PDF escaneado), intentar OCR
                print(f"⚠️  Native extraction failed: {e}")
                print("🔄 Falling back to OCR...")

        # OCR fallback (o forzado)
        try:
            texto, paginas = extract_text_pdf_ocr(file_path, dpi=ocr_dpi, lang=ocr_lang)
            print(f"✅ OCR extraction successful: {len(texto)} characters")
            return texto, paginas, TipoFuente.PDF_OCR.value
        except Exception as e:
            raise RuntimeError(
                f"Both native and OCR extraction failed for PDF: {e}"
            ) from e

    # DOCX: Extracción directa
    elif tipo_fuente == TipoFuente.DOCX.value:
        try:
            print("🔄 Extracting text from DOCX...")
            texto = extract_text_docx(file_path)
            print(f"✅ DOCX extraction successful: {len(texto)} characters")
            return texto, None, TipoFuente.DOCX.value
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed: {e}") from e

    # Imagen: OCR directo
    elif tipo_fuente == TipoFuente.IMAGE.value:
        try:
            print("🔄 Extracting text from image (OCR)...")
            texto = extract_text_image(file_path, lang=ocr_lang)
            print(f"✅ Image OCR successful: {len(texto)} characters")
            return texto, None, TipoFuente.IMAGE.value
        except Exception as e:
            raise RuntimeError(f"Image OCR extraction failed: {e}") from e

    # TXT: Lectura directa
    elif tipo_fuente == TipoFuente.TXT.value:
        try:
            print("🔄 Reading plain text file...")
            with open(file_path, "r", encoding="utf-8") as f:
                texto = f.read()
            print(f"✅ TXT reading successful: {len(texto)} characters")
            return texto, None, TipoFuente.TXT.value
        except Exception as e:
            raise RuntimeError(f"TXT reading failed: {e}") from e

    # Unknown: No debería llegar aquí si is_supported_format funcionó
    else:
        raise ValueError(f"Unknown or unsupported source type: {tipo_fuente}")


# Exportar funciones principales
__all__ = [
    "extract_text_auto",
    "detect_source",
    "is_supported_format",
    "extract_text_pdf_native",
    "extract_text_pdf_ocr",
    "extract_text_docx",
    "extract_text_image",
]


if __name__ == "__main__":
    # Test de orquestación automática
    print("=" * 60)
    print("Testing Automatic Text Extraction Orchestrator")
    print("=" * 60)

    print("\n📋 Module loaded successfully")
    print("✅ All extractors available:")
    print("   - PDF Native (pdfplumber)")
    print("   - PDF OCR (pdf2image + pytesseract)")
    print("   - DOCX (python-docx)")
    print("   - Image OCR (pytesseract)")
    print("   - TXT (built-in)")

    print("\n📋 Example usage:")
    print("""
    from pathlib import Path
    from src.extractors import extract_text_auto

    # Extracción automática (inteligente)
    texto, paginas, tipo = extract_text_auto(Path("documento.pdf"))
    print(f"Type: {tipo}, Pages: {paginas}, Length: {len(texto)}")

    # Forzar OCR (útil para comparar calidad)
    texto, paginas, tipo = extract_text_auto(
        Path("documento.pdf"),
        force_ocr=True,
        ocr_dpi=400,
        ocr_lang="spa+eng"
    )

    # Batch processing
    documentos = ["contrato.pdf", "nomina.docx", "recibo.jpg"]
    for doc in documentos:
        texto, pags, tipo = extract_text_auto(Path(doc))
        print(f"{doc}: {tipo}, {len(texto)} chars")
    """)

    print("\n✅ Extraction orchestrator ready!")
    print("⚠️  Note: Real testing requires actual documents in tests/fixtures/")
    print("⚠️  Ensure Tesseract OCR and Poppler are installed (see docs/deployment.md)")
