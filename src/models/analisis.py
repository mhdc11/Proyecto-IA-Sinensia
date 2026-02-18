"""
Modelo de Análisis - Analizador de Documentos Legales

Esquema Pydantic para la estructura de análisis extraída de documentos.
Sigue estrictamente el modelo conceptual de 8 categorías definido en la constitución.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class Fecha(BaseModel):
    """
    Representa una fecha relevante con etiqueta descriptiva

    Attributes:
        etiqueta: Tipo de fecha (ej: "Inicio", "Fin", "Vencimiento")
        valor: Fecha en formato ISO (YYYY-MM-DD) o literal si es ambigua
    """

    etiqueta: str = Field(..., description="Tipo de fecha", min_length=1)
    valor: str = Field(..., description="Fecha en ISO o literal", min_length=1)


class Importe(BaseModel):
    """
    Representa un importe económico con contexto

    Attributes:
        concepto: Descripción del importe (ej: "Salario bruto anual")
        valor: Cantidad numérica o None si no se puede extraer
        moneda: Código de moneda (EUR, USD, etc.) o None si no se especifica
    """

    concepto: str = Field(..., description="Descripción del importe", min_length=1)
    valor: Optional[float] = Field(None, description="Cantidad numérica")
    moneda: Optional[str] = Field(None, description="Código de moneda (EUR, USD, etc.)")


class Analisis(BaseModel):
    """
    Esquema completo de análisis de documento con 8 categorías obligatorias

    Este modelo sigue el Principio IV (Resultados Estructurados) y Regla R2
    (Modelo Conceptual Uniforme) de la constitución del proyecto.

    Attributes:
        tipo_documento: Clasificación general (contrato_laboral, nomina, convenio, etc.)
        partes: Lista de entidades involucradas (empresas, personas, identificadores)
        fechas: Lista de fechas relevantes con etiquetas
        importes: Lista de importes y datos económicos
        obligaciones: Lista de deberes y compromisos identificados
        derechos: Lista de facultades y beneficios identificados
        riesgos: Lista de cláusulas sensibles y alertas
        resumen_bullets: Resumen ejecutivo en 5-10 puntos clave
        notas: Observaciones adicionales (calidad OCR, advertencias, etc.)
        confianza_aprox: Confianza heurística del análisis (0.0-1.0)
    """

    # 8 Categorías Obligatorias (Regla R2 - Constitución)
    tipo_documento: str = Field(
        default="desconocido", description="Clasificación del documento", min_length=1
    )

    partes: List[str] = Field(
        default_factory=list,
        description="Entidades involucradas (empresas, personas, identificadores)",
    )

    fechas: List[Fecha] = Field(
        default_factory=list,
        description="Fechas relevantes con etiquetas (inicio, fin, plazos, vencimientos)",
    )

    importes: List[Importe] = Field(
        default_factory=list, description="Importes y datos económicos con contexto"
    )

    obligaciones: List[str] = Field(
        default_factory=list, description="Deberes y compromisos identificados"
    )

    derechos: List[str] = Field(
        default_factory=list, description="Facultades y beneficios identificados"
    )

    riesgos: List[str] = Field(
        default_factory=list,
        description="Cláusulas sensibles, penalizaciones, no competencia, confidencialidad",
    )

    resumen_bullets: List[str] = Field(
        default_factory=list, description="Resumen ejecutivo en 5-10 puntos clave"
    )

    # Metadata adicional
    notas: List[str] = Field(
        default_factory=list,
        description="Observaciones sobre calidad, limitaciones, advertencias",
    )

    confianza_aprox: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confianza heurística del análisis basada en completitud",
    )

    @validator("confianza_aprox")
    def validate_confianza(cls, v):
        """Valida que confianza_aprox esté en rango [0.0, 1.0]"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confianza_aprox debe estar entre 0.0 y 1.0")
        return v

    @validator("resumen_bullets")
    def validate_resumen_length(cls, v):
        """Valida que resumen no exceda 10 bullets (límite por chunking consolidation)"""
        if len(v) > 10:
            raise ValueError("resumen_bullets no debe exceder 10 puntos")
        return v

    def to_dict(self) -> dict:
        """
        Convierte el análisis a diccionario serializable

        Returns:
            dict: Representación completa del análisis
        """
        return self.model_dump()

    def is_complete(self) -> bool:
        """
        Verifica si el análisis tiene al menos 50% de categorías con contenido

        Returns:
            bool: True si >=4 categorías tienen datos
        """
        categorias_con_datos = sum(
            [
                bool(self.partes),
                bool(self.fechas),
                bool(self.importes),
                bool(self.obligaciones),
                bool(self.derechos),
                bool(self.riesgos),
                bool(self.resumen_bullets),
                self.tipo_documento != "desconocido",
            ]
        )
        return categorias_con_datos >= 4

    def __str__(self) -> str:
        """Representación legible del análisis"""
        return (
            f"Análisis(tipo={self.tipo_documento}, "
            f"partes={len(self.partes)}, fechas={len(self.fechas)}, "
            f"importes={len(self.importes)}, obligaciones={len(self.obligaciones)}, "
            f"derechos={len(self.derechos)}, riesgos={len(self.riesgos)}, "
            f"resumen={len(self.resumen_bullets)}, confianza={self.confianza_aprox:.2f})"
        )


if __name__ == "__main__":
    # Test de validación del schema
    print("=" * 60)
    print("Testing Análisis Schema")
    print("=" * 60)

    # Ejemplo válido
    analisis = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME CORP S.A.", "Juan Pérez García"],
        fechas=[
            Fecha(etiqueta="Inicio", valor="2026-03-01"),
            Fecha(etiqueta="Fin", valor="2027-02-28"),
        ],
        importes=[Importe(concepto="Salario bruto anual", valor=30000.0, moneda="EUR")],
        obligaciones=["No competir durante vigencia + 2 años post-finalización"],
        derechos=["30 días naturales de vacaciones anuales"],
        riesgos=["Cláusula de no competencia por 2 años"],
        resumen_bullets=[
            "Contrato laboral con renovación tácita anual",
            "Vigencia inicial: 1 marzo 2026 - 28 febrero 2027",
            "Salario bruto anual de 30.000€ en 14 pagas",
        ],
        confianza_aprox=0.95,
    )

    print("\n✅ Análisis válido creado:")
    print(analisis)
    print(f"\n✅ ¿Análisis completo? {analisis.is_complete()}")
    print(f"\n✅ To dict: {analisis.to_dict()}")

    # Ejemplo con valores por defecto
    analisis_vacio = Analisis()
    print("\n✅ Análisis vacío (defaults):")
    print(analisis_vacio)
    print(f"✅ ¿Análisis completo? {analisis_vacio.is_complete()}")

    print("\n✅ Análisis schema validation passed!")
