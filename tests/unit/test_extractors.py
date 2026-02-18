"""
Unit Tests for Text Extractors - Analizador de Documentos Legales

Tests de extracción de texto para PDF nativo, PDF OCR, DOCX, e imágenes.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from src.extraction.pdf_native import extract_pdf_native
from src.extraction.pdf_ocr import extract_pdf_ocr
from src.extraction.docx_extractor import extract_docx
from src.extraction.image_ocr import extract_image
from src.extraction.auto_extractor import extract_text_auto
from src.models.documento import TipoFuente


# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestPDFNativeExtractor:
    """Tests para extractor de PDF nativo"""

    @patch('src.extraction.pdf_native.pdfplumber')
    def test_extract_pdf_native_success(self, mock_pdfplumber):
        """Test extracción exitosa de PDF nativo"""
        # Mock PDF con texto
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Página 1 contenido"

        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Página 2 contenido"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.open.return_value = mock_pdf

        # Ejecutar extracción
        texto, paginas = extract_pdf_native(Path("dummy.pdf"))

        # Verificar
        assert "Página 1 contenido" in texto
        assert "Página 2 contenido" in texto
        assert paginas == 2

    @patch('src.extraction.pdf_native.pdfplumber')
    def test_extract_pdf_native_empty(self, mock_pdfplumber):
        """Test PDF sin texto (debería retornar vacío)"""
        # Mock PDF sin texto
        mock_page = Mock()
        mock_page.extract_text.return_value = None

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.open.return_value = mock_pdf

        # Ejecutar
        texto, paginas = extract_pdf_native(Path("empty.pdf"))

        # Verificar
        assert texto == ""
        assert paginas == 1

    @patch('src.extraction.pdf_native.pdfplumber')
    def test_extract_pdf_native_error(self, mock_pdfplumber):
        """Test manejo de errores en PDF corrupto"""
        mock_pdfplumber.open.side_effect = Exception("PDF corrupto")

        # Ejecutar y verificar excepción
        with pytest.raises(Exception) as exc_info:
            extract_pdf_native(Path("corrupto.pdf"))

        assert "PDF corrupto" in str(exc_info.value)


class TestPDFOCRExtractor:
    """Tests para extractor de PDF con OCR"""

    @patch('src.extraction.pdf_ocr.convert_from_path')
    @patch('src.extraction.pdf_ocr.pytesseract')
    def test_extract_pdf_ocr_success(self, mock_pytesseract, mock_convert):
        """Test extracción exitosa con OCR"""
        # Mock imágenes convertidas
        mock_image1 = Mock()
        mock_image2 = Mock()
        mock_convert.return_value = [mock_image1, mock_image2]

        # Mock OCR
        mock_pytesseract.image_to_string.side_effect = [
            "Texto página 1",
            "Texto página 2"
        ]

        # Ejecutar
        texto, paginas = extract_pdf_ocr(Path("escaneado.pdf"), dpi=300, lang="spa")

        # Verificar
        assert "Texto página 1" in texto
        assert "Texto página 2" in texto
        assert paginas == 2
        mock_pytesseract.image_to_string.assert_called()

    @patch('src.extraction.pdf_ocr.convert_from_path')
    @patch('src.extraction.pdf_ocr.pytesseract')
    def test_extract_pdf_ocr_multi_lang(self, mock_pytesseract, mock_convert):
        """Test OCR con múltiples idiomas"""
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_pytesseract.image_to_string.return_value = "Mixed text"

        # Ejecutar con spa+eng
        texto, paginas = extract_pdf_ocr(Path("mixed.pdf"), lang="spa+eng")

        # Verificar que se llamó con el idioma correcto
        call_args = mock_pytesseract.image_to_string.call_args
        assert call_args[1]['lang'] == "spa+eng"


class TestDOCXExtractor:
    """Tests para extractor de DOCX"""

    @patch('src.extraction.docx_extractor.Document')
    def test_extract_docx_success(self, mock_document_class):
        """Test extracción exitosa de DOCX"""
        # Mock párrafos
        mock_para1 = Mock()
        mock_para1.text = "Primer párrafo"

        mock_para2 = Mock()
        mock_para2.text = "Segundo párrafo"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]

        mock_document_class.return_value = mock_doc

        # Ejecutar
        texto = extract_docx(Path("documento.docx"))

        # Verificar
        assert "Primer párrafo" in texto
        assert "Segundo párrafo" in texto

    @patch('src.extraction.docx_extractor.Document')
    def test_extract_docx_empty_paragraphs(self, mock_document_class):
        """Test DOCX con párrafos vacíos"""
        # Mock con párrafos vacíos mezclados
        mock_para1 = Mock()
        mock_para1.text = "Contenido"

        mock_para2 = Mock()
        mock_para2.text = ""

        mock_para3 = Mock()
        mock_para3.text = "Más contenido"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]

        mock_document_class.return_value = mock_doc

        # Ejecutar
        texto = extract_docx(Path("con_vacios.docx"))

        # Verificar que filtra párrafos vacíos
        assert "Contenido" in texto
        assert "Más contenido" in texto


class TestImageOCRExtractor:
    """Tests para extractor de imágenes con OCR"""

    @patch('src.extraction.image_ocr.Image')
    @patch('src.extraction.image_ocr.pytesseract')
    def test_extract_image_success(self, mock_pytesseract, mock_image_class):
        """Test extracción exitosa de imagen"""
        mock_image = Mock()
        mock_image_class.open.return_value = mock_image

        mock_pytesseract.image_to_string.return_value = "Texto extraído de imagen"

        # Ejecutar
        texto = extract_image(Path("documento.jpg"), lang="spa")

        # Verificar
        assert texto == "Texto extraído de imagen"
        mock_pytesseract.image_to_string.assert_called_once()

    @patch('src.extraction.image_ocr.Image')
    @patch('src.extraction.image_ocr.pytesseract')
    def test_extract_image_png(self, mock_pytesseract, mock_image_class):
        """Test con imagen PNG"""
        mock_image = Mock()
        mock_image_class.open.return_value = mock_image
        mock_pytesseract.image_to_string.return_value = "Texto PNG"

        # Ejecutar
        texto = extract_image(Path("documento.png"))

        # Verificar
        assert texto == "Texto PNG"


class TestAutoExtractor:
    """Tests para extractor automático (orquestador)"""

    @patch('src.extraction.auto_extractor.extract_pdf_native')
    def test_auto_extractor_pdf_native_success(self, mock_pdf_native):
        """Test auto con PDF nativo (con texto)"""
        mock_pdf_native.return_value = ("Texto del PDF", 5)

        # Ejecutar
        texto, paginas, tipo = extract_text_auto(Path("documento.pdf"))

        # Verificar que usó PDF nativo
        assert texto == "Texto del PDF"
        assert paginas == 5
        assert tipo == TipoFuente.PDF_NATIVE
        mock_pdf_native.assert_called_once()

    @patch('src.extraction.auto_extractor.extract_pdf_ocr')
    @patch('src.extraction.auto_extractor.extract_pdf_native')
    def test_auto_extractor_pdf_fallback_ocr(self, mock_pdf_native, mock_pdf_ocr):
        """Test auto con PDF escaneado (fallback a OCR)"""
        # PDF nativo retorna vacío (sin texto)
        mock_pdf_native.return_value = ("", 3)

        # OCR retorna texto
        mock_pdf_ocr.return_value = ("Texto por OCR", 3)

        # Ejecutar
        texto, paginas, tipo = extract_text_auto(Path("escaneado.pdf"))

        # Verificar que hizo fallback a OCR
        assert texto == "Texto por OCR"
        assert tipo == TipoFuente.PDF_OCR
        mock_pdf_native.assert_called_once()
        mock_pdf_ocr.assert_called_once()

    @patch('src.extraction.auto_extractor.extract_docx')
    def test_auto_extractor_docx(self, mock_docx):
        """Test auto con DOCX"""
        mock_docx.return_value = "Texto del DOCX"

        # Ejecutar
        texto, paginas, tipo = extract_text_auto(Path("documento.docx"))

        # Verificar
        assert texto == "Texto del DOCX"
        assert paginas is None  # DOCX no tiene páginas
        assert tipo == TipoFuente.DOCX
        mock_docx.assert_called_once()

    @patch('src.extraction.auto_extractor.extract_image')
    def test_auto_extractor_image(self, mock_image):
        """Test auto con imagen"""
        mock_image.return_value = "Texto de imagen"

        # Ejecutar
        texto, paginas, tipo = extract_text_auto(Path("documento.jpg"))

        # Verificar
        assert texto == "Texto de imagen"
        assert paginas is None
        assert tipo == TipoFuente.IMAGE
        mock_image.assert_called_once()

    def test_auto_extractor_unsupported_format(self):
        """Test con formato no soportado"""
        # Ejecutar con extensión no soportada
        with pytest.raises(ValueError) as exc_info:
            extract_text_auto(Path("documento.xyz"))

        assert "Formato no soportado" in str(exc_info.value)


class TestTextNormalization:
    """Tests para normalización de texto"""

    @patch('src.extraction.auto_extractor.extract_pdf_native')
    def test_normalization_whitespace(self, mock_pdf_native):
        """Test normalización de espacios en blanco"""
        # Texto con espacios múltiples y saltos de línea
        mock_pdf_native.return_value = ("Texto  con    espacios\n\n\nmúltiples\t\ttabs", 1)

        texto, _, _ = extract_text_auto(Path("test.pdf"))

        # Verificar normalización (espacios múltiples → espacio simple)
        assert "  " not in texto  # No dobles espacios
        assert "\n\n\n" not in texto  # No triples saltos

    @patch('src.extraction.auto_extractor.extract_pdf_native')
    def test_normalization_empty_result(self, mock_pdf_native):
        """Test con resultado vacío tras normalización"""
        mock_pdf_native.return_value = ("   \n\n\t\t   ", 1)

        texto, _, _ = extract_text_auto(Path("vacio.pdf"))

        # Verificar que retorna cadena vacía limpia
        assert texto == ""


# Fixtures de datos de ejemplo
@pytest.fixture
def sample_text_fixture():
    """Fixture de texto simple para tests"""
    return """
    Contrato de Trabajo

    Entre ACME Corp S.A. y Juan Pérez García
    Fecha de inicio: 2026-03-01
    Salario: 30.000 EUR anuales
    """


@pytest.fixture
def sample_pdf_content():
    """Fixture de contenido PDF simulado"""
    return {
        'pages': 3,
        'text': "Este es un documento legal con múltiples páginas.\n"
                "Contiene información sobre partes, fechas e importes.\n"
                "Página 1, Página 2, Página 3."
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
