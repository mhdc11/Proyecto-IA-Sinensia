"""
Image OCR Text Extractor - Analizador de Documentos Legales

Extractor de texto para imágenes (PNG, JPG, TIFF) usando pytesseract OCR.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from pathlib import Path
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("⚠️  pytesseract or PIL not available. Install with: pip install pytesseract pillow")


# Extensiones de imagen soportadas
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}


def extract_text_image(file_path: Path, lang: str = "spa") -> str:
    """
    Extrae texto de una imagen usando OCR (pytesseract)

    Args:
        file_path: Ruta a la imagen
        lang: Idioma(s) de Tesseract (default: 'spa', options: 'eng', 'spa+eng')

    Returns:
        str: Texto extraído de la imagen

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo no es una imagen soportada
        RuntimeError: Si pytesseract no está instalado o falla el OCR

    Example:
        >>> from pathlib import Path
        >>> texto = extract_text_image(Path("recibo.jpg"))
        >>> print(f"Extracted {len(texto)} characters")
        Extracted 850 characters
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")

    if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"File is not a supported image format. "
            f"Supported: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )

    if not PYTESSERACT_AVAILABLE:
        raise RuntimeError(
            "pytesseract not installed. Install with: pip install pytesseract pillow\n"
            "Also requires Tesseract OCR: see docs/deployment.md"
        )

    try:
        # Cargar imagen con PIL
        print(f"🔄 Loading image: {file_path.name}...")
        image = Image.open(file_path)

        # Convertir a RGB si es necesario (algunos formatos tienen canales alpha)
        if image.mode not in ["RGB", "L"]:
            print(f"   Converting image from {image.mode} to RGB...")
            image = image.convert("RGB")

        # Aplicar OCR
        print(f"🔄 Running OCR (lang={lang})...")
        text = pytesseract.image_to_string(image, lang=lang)

        if not text.strip():
            raise RuntimeError(
                f"OCR did not extract any text from image. "
                f"Image may be of very low quality, blank, or not contain text."
            )

        print(f"✅ OCR complete: {len(text)} characters extracted")
        return text.strip()

    except pytesseract.TesseractNotFoundError as e:
        raise RuntimeError(
            f"Tesseract OCR not installed or not in PATH: {e}\n"
            f"See docs/deployment.md for installation instructions"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error during OCR extraction from image: {e}") from e


def extract_text_image_with_preprocessing(
    file_path: Path, lang: str = "spa", enhance: bool = True
) -> str:
    """
    Extrae texto de una imagen con preprocesamiento opcional para mejorar OCR

    Args:
        file_path: Ruta a la imagen
        lang: Idioma(s) de Tesseract
        enhance: Si True, aplica mejoras de imagen (contraste, nitidez)

    Returns:
        str: Texto extraído

    Example:
        >>> texto = extract_text_image_with_preprocessing(
        ...     Path("recibo_borroso.jpg"),
        ...     enhance=True
        ... )
    """
    if not PYTESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract not installed")

    from PIL import ImageEnhance, ImageFilter

    image = Image.open(file_path)

    # Convertir a RGB si es necesario
    if image.mode not in ["RGB", "L"]:
        image = image.convert("RGB")

    if enhance:
        print("🔄 Enhancing image for better OCR...")

        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # Aumentar nitidez
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)

        # Aplicar filtro de mediana para reducir ruido
        image = image.filter(ImageFilter.MedianFilter(size=3))

    # Aplicar OCR
    text = pytesseract.image_to_string(image, lang=lang)

    if not text.strip():
        raise RuntimeError("No text extracted after preprocessing")

    return text.strip()


if __name__ == "__main__":
    # Test de extracción de imágenes
    print("=" * 60)
    print("Testing Image OCR Text Extraction")
    print("=" * 60)

    print("\n📋 Module loaded successfully")
    print(f"✅ pytesseract available: {PYTESSERACT_AVAILABLE}")
    print(f"✅ Supported extensions: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}")

    print("\n📋 Example usage:")
    print("""
    from pathlib import Path
    from src.extractors.image_extractor import extract_text_image

    # Extraer texto simple
    texto = extract_text_image(Path("recibo.jpg"))
    print(f"Extracted: {texto[:100]}...")

    # Con idioma inglés
    texto = extract_text_image(Path("invoice.png"), lang="eng")

    # Con preprocesamiento para imágenes de baja calidad
    texto = extract_text_image_with_preprocessing(
        Path("documento_borroso.tiff"),
        lang="spa",
        enhance=True
    )
    """)

    # Test de validación básica
    print("\n📋 Testing error handling:")
    try:
        extract_text_image(Path("nonexistent.png"))
        print("❌ Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("✅ Correctly raised FileNotFoundError")

    try:
        extract_text_image(Path("not_an_image.txt"))
        print("❌ Should have raised ValueError")
    except ValueError:
        print("✅ Correctly raised ValueError for non-image file")

    print("\n✅ Image OCR extractor ready!")
    print("⚠️  Note: Real testing requires:")
    print("   1. Actual image files in tests/fixtures/")
    print("   2. Tesseract OCR installed (see docs/deployment.md)")
