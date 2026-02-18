"""
Modelo de Dupla - Analizador de Documentos Legales

Esquema Pydantic para la asociación documento ↔ análisis (dupla).
Representa el concepto fundamental del sistema de historial.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.models.documento import Documento, TipoFuente
from src.models.analisis import Analisis


class EstadoDupla(str, Enum):
    """
    Enumeración de estados posibles de una dupla

    Estados:
        VALIDO: Análisis completo y sin advertencias
        CON_ADVERTENCIAS: Análisis completo pero con notas/advertencias
        INCOMPLETO: Análisis con <50% de categorías pobladas
    """

    VALIDO = "valido"
    CON_ADVERTENCIAS = "con_advertencias"
    INCOMPLETO = "incompleto"


class Dupla(BaseModel):
    """
    Asociación entre un documento y su análisis (dupla)

    Este es el concepto fundamental del sistema de historial.
    Cada dupla representa un análisis completo de un documento específico.

    Attributes:
        id: Identificador único (mismo que documento.id para vinculación)
        documento: Metadata del documento analizado
        analisis: Resultado del análisis estructurado en 8 categorías
        ts_creacion: Timestamp de creación de la dupla
        ts_actualizacion: Timestamp de última actualización
        estado: Estado del análisis (valido, con_advertencias, incompleto)
    """

    id: str = Field(
        ...,
        description="ID único (mismo que documento.id para vinculación)",
        min_length=16,
        max_length=16,
    )

    documento: Documento = Field(..., description="Metadata del documento analizado")

    analisis: Analisis = Field(
        ..., description="Resultado del análisis estructurado en 8 categorías"
    )

    ts_creacion: datetime = Field(
        default_factory=datetime.now, description="Timestamp de creación de la dupla"
    )

    ts_actualizacion: datetime = Field(
        default_factory=datetime.now, description="Timestamp de última actualización"
    )

    estado: EstadoDupla = Field(
        default=EstadoDupla.VALIDO, description="Estado del análisis"
    )

    def model_post_init(self, __context):
        """
        Post-init validation: Auto-determina el estado basado en el análisis

        Si analisis.is_complete() es False → INCOMPLETO
        Si analisis.notas tiene elementos → CON_ADVERTENCIAS
        Caso contrario → VALIDO
        """
        if not self.analisis.is_complete():
            self.estado = EstadoDupla.INCOMPLETO
        elif self.analisis.notas:
            self.estado = EstadoDupla.CON_ADVERTENCIAS
        else:
            self.estado = EstadoDupla.VALIDO

    def to_dict(self) -> dict:
        """
        Convierte la dupla a diccionario serializable

        Returns:
            dict: Representación completa con documento, análisis y metadata
        """
        return {
            "id": self.id,
            "documento": self.documento.to_dict(),
            "analisis": self.analisis.to_dict(),
            "ts_creacion": self.ts_creacion.isoformat(),
            "ts_actualizacion": self.ts_actualizacion.isoformat(),
            "estado": self.estado.value,
        }

    def actualizar(self) -> None:
        """
        Actualiza el timestamp de última actualización al momento actual
        """
        self.ts_actualizacion = datetime.now()

    def __str__(self) -> str:
        """Representación legible de la dupla"""
        return (
            f"Dupla(id={self.id}, documento={self.documento.nombre}, "
            f"tipo_doc={self.analisis.tipo_documento}, estado={self.estado.value}, "
            f"creado={self.ts_creacion.strftime('%Y-%m-%d %H:%M')})"
        )


if __name__ == "__main__":
    # Test de validación del schema
    print("=" * 60)
    print("Testing Dupla Schema")
    print("=" * 60)

    # Crear documento de ejemplo
    from src.models.analisis import Fecha, Importe

    doc = Documento(
        id="a1b2c3d4e5f6g7h8",
        nombre="contrato_laboral_2024.pdf",
        tipo_fuente=TipoFuente.PDF_NATIVE,
        paginas=12,
        bytes=245760,
        idioma_detectado="es",
    )

    # Crear análisis de ejemplo (completo)
    analisis_completo = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME CORP S.A.", "Juan Pérez García"],
        fechas=[
            Fecha(etiqueta="Inicio", valor="2026-03-01"),
            Fecha(etiqueta="Fin", valor="2027-02-28"),
        ],
        importes=[Importe(concepto="Salario bruto anual", valor=30000.0, moneda="EUR")],
        obligaciones=["No competir durante vigencia"],
        derechos=["30 días de vacaciones"],
        riesgos=["Cláusula de no competencia"],
        resumen_bullets=["Contrato laboral anual", "Salario 30.000€"],
        confianza_aprox=0.95,
    )

    # Crear dupla válida
    dupla = Dupla(id="a1b2c3d4e5f6g7h8", documento=doc, analisis=analisis_completo)

    print("\n✅ Dupla válida creada:")
    print(dupla)
    print(f"✅ Estado auto-determinado: {dupla.estado.value}")
    print(f"\n✅ To dict: {dupla.to_dict()}")

    # Crear análisis incompleto (sin contenido)
    analisis_incompleto = Analisis()

    # Crear dupla incompleta
    dupla_incompleta = Dupla(id="a1b2c3d4e5f6g7h8", documento=doc, analisis=analisis_incompleto)

    print("\n✅ Dupla incompleta creada:")
    print(dupla_incompleta)
    print(f"✅ Estado auto-determinado: {dupla_incompleta.estado.value}")

    # Test actualización
    dupla.actualizar()
    print(f"\n✅ Dupla actualizada: {dupla.ts_actualizacion}")

    print("\n✅ Dupla schema validation passed!")
