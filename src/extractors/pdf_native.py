"""
PDF Native Text Extractor - Analizador de Documentos Legales

Extractor de texto para PDFs con texto embebido usando pdfplumber.
Para PDFs escaneados (sin texto), usar pdf_ocr.py en su lugar.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from pathlib import Path
from typing import Tuple, Optional
import pdfplumber


def extract_text_pdf_native(file_path: Path) -> Tuple[str, int]:
    """
    Extrae texto de un PDF nativo (con texto embebido) usando pdfplumber

    Args:
        file_path: Ruta al archivo PDF

    Returns:
        Tuple[str, int]: (texto_extraído, número_de_páginas)

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo no es un PDF válido
        RuntimeError: Si pdfplumber falla durante la extracción

    Example:
        >>> from pathlib import Path
        >>> texto, paginas = extract_text_pdf_native(Path("contrato.pdf"))
        >>> print(f"Extraídas {paginas} páginas, {len(texto)} caracteres")
        Extraídas 12 páginas, 24560 caracteres
    """
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {file_path}")

    try:
        extracted_text = []
        page_count = 0

        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)

            # Extraer texto de cada página
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()

                if page_text:
                    # Preservar saltos de línea básicos y añadir separador de página
                    extracted_text.append(page_text.strip())
                    extracted_text.append(f"\n--- Página {page_num} ---\n")

        # Unir todo el texto
        full_text = "\n".join(extracted_text)

        # Verificar si se extrajo texto (PDFs escaneados pueden no tener texto embebido)
        if not full_text.strip():
            raise RuntimeError(
                f"No text extracted from PDF. File may be scanned/image-based. "
                f"Use pdf_ocr.py instead."
            )

        return full_text, page_count

    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
        raise ValueError(f"Invalid or corrupted PDF file: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Error extracting text from PDF: {e}") from e


def has_extractable_text(file_path: Path, min_chars: int = 50) -> bool:
    """
    Verifica si un PDF tiene texto extraíble (no es escaneado)

    Args:
        file_path: Ruta al PDF
        min_chars: Número mínimo de caracteres para considerar que hay texto (default: 50)

    Returns:
        bool: True si el PDF tiene texto extraíble, False si es escaneado/imagen

    Example:
        >>> has_extractable_text(Path("contrato_nativo.pdf"))
        True
        >>> has_extractable_text(Path("contrato_escaneado.pdf"))
        False
    """
    try:
        texto, _ = extract_text_pdf_native(file_path)
        return len(texto.strip()) >= min_chars
    except RuntimeError:
        # Si falla la extracción, asumir que es escaneado
        return False
    except Exception:
        # Cualquier otro error, asumir escaneado
        return False


if __name__ == "__main__":
    # Test de extracción de PDF nativo
    print("=" * 60)
    print("Testing PDF Native Text Extraction")
    print("=" * 60)

    # Nota: Para testing real, necesitarías un PDF de ejemplo
    # Aquí mostramos cómo se usaría

    print("\n📋 Module loaded successfully")
    print("✅ Function 'extract_text_pdf_native' available")
    print("✅ Function 'has_extractable_text' available")

    print("\n📋 Example usage:")
    print("""
    from pathlib import Path
    from src.extractors.pdf_native import extract_text_pdf_native

    # Extraer texto de PDF nativo
    texto, paginas = extract_text_pdf_native(Path("contrato.pdf"))
    print(f"Extracted {paginas} pages")
    print(f"Text length: {len(texto)} characters")

    # Verificar si PDF tiene texto
    if has_extractable_text(Path("documento.pdf")):
        print("PDF has extractable text (native)")
    else:
        print("PDF is scanned, use OCR instead")
    """)

    # Test de validación básica
    print("\n📋 Testing error handling:")
    try:
        extract_text_pdf_native(Path("nonexistent.pdf"))
        print("❌ Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"✅ Correctly raised FileNotFoundError")

    try:
        extract_text_pdf_native(Path("not_a_pdf.txt"))
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError for non-PDF file")

    print("\n✅ PDF native extractor ready!")
    print("⚠️  Note: Real testing requires actual PDF files in tests/fixtures/")
