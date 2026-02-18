"""
Modelo de Documento - Analizador de Documentos Legales

Esquema Pydantic para metadata de documentos cargados por el usuario.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator


class TipoFuente(str, Enum):
    """
    Enumeración de tipos de fuente de documento

    Permite identificar el método de extracción usado para obtener el texto.
    """

    PDF_NATIVE = "pdf_native"  # PDF con texto embebido (pdfplumber)
    PDF_OCR = "pdf_ocr"  # PDF escaneado procesado con OCR
    DOCX = "docx"  # Microsoft Word DOCX
    IMAGE = "image"  # Imagen (PNG, JPG, TIFF) procesada con OCR
    TXT = "txt"  # Texto plano
    UNKNOWN = "unknown"  # Tipo no reconocido


class Documento(BaseModel):
    """
    Esquema de documento con metadata esencial

    Attributes:
        id: Identificador único (SHA-256 hash truncado a 16 caracteres)
        nombre: Nombre del archivo original
        tipo_fuente: Tipo de fuente del documento (PDF nativo, OCR, DOCX, etc.)
        paginas: Número de páginas (None si no aplica, ej: imágenes sueltas)
        bytes: Tamaño del archivo en bytes
        idioma_detectado: Idioma detectado del contenido ('es', 'en', 'unknown', etc.)
        ts_ingesta: Timestamp de cuando se cargó/procesó el documento
    """

    id: str = Field(
        ..., description="ID único (SHA-256 truncado a 16 chars)", min_length=16, max_length=16
    )

    nombre: str = Field(..., description="Nombre del archivo original", min_length=1)

    tipo_fuente: TipoFuente = Field(
        default=TipoFuente.UNKNOWN, description="Tipo de fuente del documento"
    )

    paginas: Optional[int] = Field(
        None, ge=1, description="Número de páginas (None si no aplica)"
    )

    bytes: Optional[int] = Field(None, ge=0, description="Tamaño del archivo en bytes")

    idioma_detectado: Optional[str] = Field(
        None, description="Idioma detectado (es, en, unknown, etc.)"
    )

    ts_ingesta: datetime = Field(
        default_factory=datetime.now, description="Timestamp de ingesta del documento"
    )

    @validator("id")
    def validate_id_length(cls, v):
        """Valida que el ID tenga exactamente 16 caracteres (SHA-256 truncado)"""
        if len(v) != 16:
            raise ValueError("El ID debe tener exactamente 16 caracteres")
        return v

    def to_dict(self) -> dict:
        """
        Convierte el documento a diccionario serializable

        Returns:
            dict: Representación completa del documento con timestamp en ISO format
        """
        data = self.model_dump()
        # Convertir datetime a ISO string para JSON serialization
        data["ts_ingesta"] = self.ts_ingesta.isoformat()
        return data

    def __str__(self) -> str:
        """Representación legible del documento"""
        return (
            f"Documento(id={self.id}, nombre={self.nombre}, "
            f"tipo={self.tipo_fuente.value}, paginas={self.paginas}, "
            f"bytes={self.bytes}, idioma={self.idioma_detectado})"
        )


if __name__ == "__main__":
    # Test de validación del schema
    print("=" * 60)
    print("Testing Documento Schema")
    print("=" * 60)

    # Ejemplo válido
    doc = Documento(
        id="a1b2c3d4e5f6g7h8",
        nombre="contrato_laboral_2024.pdf",
        tipo_fuente=TipoFuente.PDF_NATIVE,
        paginas=12,
        bytes=245760,
        idioma_detectado="es",
    )

    print("\n✅ Documento válido creado:")
    print(doc)
    print(f"\n✅ To dict: {doc.to_dict()}")

    # Ejemplo con valores mínimos
    doc_minimo = Documento(id="1234567890abcdef", nombre="recibo.jpg", tipo_fuente=TipoFuente.IMAGE)

    print("\n✅ Documento mínimo creado:")
    print(doc_minimo)

    # Validación de ID incorrecto (debe fallar)
    try:
        doc_invalido = Documento(id="corto", nombre="test.pdf")
        print("\n❌ ERROR: Debería haber fallado con ID corto")
    except Exception as e:
        print(f"\n✅ Validación correcta: ID corto rechazado - {e}")

    print("\n✅ Documento schema validation passed!")
