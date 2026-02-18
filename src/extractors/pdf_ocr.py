"""
PDF OCR Text Extractor - Analizador de Documentos Legales

Extractor de texto para PDFs escaneados (sin texto embebido) usando OCR.
Convierte páginas PDF a imágenes con pdf2image y aplica OCR con pytesseract.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from pathlib import Path
from typing import Tuple, Optional
import tempfile

try:
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFPageCountError, PDFInfoNotInstalledError
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("⚠️  pdf2image not available. Install with: pip install pdf2image")

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("⚠️  pytesseract not available. Install with: pip install pytesseract")


def extract_text_pdf_ocr(
    file_path: Path, dpi: int = 300, lang: str = "spa"
) -> Tuple[str, int]:
    """
    Extrae texto de un PDF escaneado usando OCR (pdf2image + pytesseract)

    Args:
        file_path: Ruta al archivo PDF escaneado
        dpi: Resolución DPI para renderizar páginas (default: 300, range: 200-600)
        lang: Idioma(s) de Tesseract (default: 'spa', options: 'eng', 'spa+eng')

    Returns:
        Tuple[str, int]: (texto_extraído, número_de_páginas)

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo no es un PDF válido o si DPI está fuera de rango
        RuntimeError: Si OCR falla o dependencias no están instaladas

    Example:
        >>> from pathlib import Path
        >>> texto, paginas = extract_text_pdf_ocr(Path("nomina_escaneada.pdf"))
        >>> print(f"OCR procesó {paginas} páginas, {len(texto)} caracteres")
        OCR procesó 5 páginas, 12340 caracteres
    """
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {file_path}")

    if not (200 <= dpi <= 600):
        raise ValueError(f"DPI must be between 200 and 600, got {dpi}")

    if not PDF2IMAGE_AVAILABLE:
        raise RuntimeError(
            "pdf2image not installed. Install with: pip install pdf2image\n"
            "Also requires poppler: see docs/deployment.md for installation instructions"
        )

    if not PYTESSERACT_AVAILABLE:
        raise RuntimeError(
            "pytesseract not installed. Install with: pip install pytesseract\n"
            "Also requires Tesseract OCR: see docs/deployment.md"
        )

    try:
        # Convertir PDF a imágenes (una por página)
        print(f"🔄 Converting PDF to images at {dpi} DPI...")
        images = convert_from_path(str(file_path), dpi=dpi)
        page_count = len(images)

        print(f"🔄 Running OCR on {page_count} pages (lang={lang})...")
        extracted_text = []

        # Procesar cada página con OCR
        for page_num, image in enumerate(images, start=1):
            print(f"   Processing page {page_num}/{page_count}...", end="\r")

            # Aplicar OCR a la imagen
            page_text = pytesseract.image_to_string(image, lang=lang)

            if page_text.strip():
                extracted_text.append(page_text.strip())
                extracted_text.append(f"\n--- Página {page_num} (OCR) ---\n")

        print()  # Salto de línea final

        # Unir todo el texto
        full_text = "\n".join(extracted_text)

        if not full_text.strip():
            raise RuntimeError(
                f"OCR did not extract any text from PDF. "
                f"Document may be of very low quality or completely blank."
            )

        print(f"✅ OCR complete: {len(full_text)} characters extracted")
        return full_text, page_count

    except PDFPageCountError as e:
        raise ValueError(f"Invalid PDF file (could not count pages): {e}") from e
    except PDFInfoNotInstalledError as e:
        raise RuntimeError(
            f"Poppler not installed or not in PATH: {e}\n"
            f"See docs/deployment.md for installation instructions"
        ) from e
    except pytesseract.TesseractNotFoundError as e:
        raise RuntimeError(
            f"Tesseract OCR not installed or not in PATH: {e}\n"
            f"See docs/deployment.md for installation instructions"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error during OCR extraction: {e}") from e


if __name__ == "__main__":
    # Test de extracción de PDF con OCR
    print("=" * 60)
    print("Testing PDF OCR Text Extraction")
    print("=" * 60)

    print("\n📋 Module loaded successfully")
    print(f"✅ pdf2image available: {PDF2IMAGE_AVAILABLE}")
    print(f"✅ pytesseract available: {PYTESSERACT_AVAILABLE}")

    print("\n📋 Example usage:")
    print("""
    from pathlib import Path
    from src.extractors.pdf_ocr import extract_text_pdf_ocr

    # Extraer texto de PDF escaneado
    texto, paginas = extract_text_pdf_ocr(
        Path("nomina_escaneada.pdf"),
        dpi=300,
        lang="spa"
    )
    print(f"OCR processed {paginas} pages")
    print(f"Text length: {len(texto)} characters")

    # Para documentos en inglés
    texto, paginas = extract_text_pdf_ocr(
        Path("contract_english.pdf"),
        dpi=400,
        lang="eng"
    )

    # Para documentos bilingües
    texto, paginas = extract_text_pdf_ocr(
        Path("documento_mixto.pdf"),
        lang="spa+eng"
    )
    """)

    # Test de validación básica
    print("\n📋 Testing error handling:")
    try:
        extract_text_pdf_ocr(Path("nonexistent.pdf"))
        print("❌ Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("✅ Correctly raised FileNotFoundError")

    try:
        extract_text_pdf_ocr(Path("test.txt"))
        print("❌ Should have raised ValueError")
    except ValueError:
        print("✅ Correctly raised ValueError for non-PDF file")

    try:
        extract_text_pdf_ocr(Path("test.pdf"), dpi=1000)
        print("❌ Should have raised ValueError for invalid DPI")
    except (ValueError, FileNotFoundError):
        print("✅ Correctly raised ValueError for invalid DPI")

    print("\n✅ PDF OCR extractor ready!")
    print("⚠️  Note: Real testing requires:")
    print("   1. Actual scanned PDF files in tests/fixtures/")
    print("   2. Tesseract OCR installed (see docs/deployment.md)")
    print("   3. Poppler installed (see docs/deployment.md)")
