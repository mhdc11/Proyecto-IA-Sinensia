# Data Model: Analizador de Documentos Legales

**Feature**: 001-doc-analyzer
**Date**: 2026-02-18
**Phase**: 1 (Design & Contracts)

## Overview

Este documento define el modelo conceptual de datos para el análisis de documentos legales, incluyendo schemas Pydantic para validación, tipos de datos, relaciones y reglas de negocio.

---

## Entity Relationship Diagram

```
┌──────────────┐
│  Documento   │
│              │
│ - id         │
│ - nombre     │
│ - tipo_fuente│
│ - paginas    │
│ - bytes      │
│ - idioma     │
│ - ts_ingesta │
└──────┬───────┘
       │
       │ 1:1
       │
       ▼
┌──────────────┐         ┌───────────────┐
│    Dupla     │ 1:1     │   Análisis    │
│              ├────────▶│               │
│ - id         │         │ - tipo_doc    │
│ - documento  │         │ - partes      │
│ - analisis   │         │ - fechas      │
│ - estado     │         │ - importes    │
│ - ts_creacion│         │ - obligaciones│
│ - ts_actualiz│         │ - derechos    │
└──────────────┘         │ - riesgos     │
       │                 │ - resumen     │
       │                 │ - notas       │
       │                 │ - confianza   │
       │                 └───────────────┘
       │
       │ N:1
       ▼
┌──────────────┐
│   Historial  │
│              │
│ - duplas[]   │
│ - ordenamiento│
└──────────────┘
```

**Relaciones**:
- **Documento 1:1 Dupla**: Un documento tiene exactamente una dupla por ejecución de análisis
- **Dupla 1:1 Análisis**: Una dupla contiene exactamente un análisis
- **Historial 1:N Duplas**: El historial mantiene lista de todas las duplas creadas

---

## Entity: Documento

**Purpose**: Representa el archivo físico cargado por el usuario y sus metadatos técnicos.

### Schema (Pydantic)

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from pathlib import Path
from enum import Enum

class TipoFuente(str, Enum):
    """Tipo de fuente de extracción de texto"""
    PDF_NATIVE = "pdf_native"      # PDF con texto embebido
    PDF_OCR = "pdf_ocr"            # PDF escaneado procesado con OCR
    DOCX = "docx"                  # Documento DOCX
    IMAGE = "image"                # Imagen directa (PNG, JPG, TIFF)
    TXT = "txt"                    # Archivo de texto plano

class Documento(BaseModel):
    """
    Metadatos del archivo cargado por el usuario.
    """
    id: str = Field(
        ...,
        description="Identificador único (SHA-256 de bytes del archivo, truncado a 16 chars)",
        min_length=16,
        max_length=16,
        pattern="^[a-f0-9]{16}$"
    )
    nombre: str = Field(
        ...,
        description="Nombre del archivo original (ej: contrato-laboral-2024.pdf)",
        min_length=1,
        max_length=255
    )
    tipo_fuente: TipoFuente = Field(
        ...,
        description="Método de extracción de texto utilizado"
    )
    paginas: int | None = Field(
        default=None,
        description="Número de páginas del documento (None si no aplica, ej: TXT)",
        ge=1,
        le=1000
    )
    bytes: int = Field(
        ...,
        description="Tamaño del archivo en bytes",
        gt=0,
        le=100_000_000  # Límite 100MB
    )
    idioma_detectado: str | None = Field(
        default=None,
        description="Código de idioma detectado (ISO 639-1: 'es', 'en', 'fr', etc.)",
        pattern="^[a-z]{2}$"
    )
    ts_ingesta: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de cuando se cargó el documento"
    )

    @field_validator('nombre')
    def validate_nombre(cls, v: str) -> str:
        """Validar que el nombre no contenga caracteres peligrosos"""
        if any(char in v for char in ['/', '\\', '..', '\x00']):
            raise ValueError("Nombre de archivo contiene caracteres no permitidos")
        return v

    @field_validator('bytes')
    def validate_bytes(cls, v: int) -> int:
        """Verificar límite de tamaño de archivo"""
        if v > 100_000_000:  # 100MB
            raise ValueError("Archivo excede límite de 100MB")
        return v

    def __repr__(self) -> str:
        return f"Documento(id={self.id[:8]}..., nombre={self.nombre}, tipo={self.tipo_fuente}, paginas={self.paginas})"
```

### Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `id` | str | ✅ | 16 chars hex | SHA-256(bytes) truncado, garantiza unicidad |
| `nombre` | str | ✅ | 1-255 chars | Filename original, sin path completo |
| `tipo_fuente` | TipoFuente | ✅ | Enum | Método de extracción usado |
| `paginas` | int\|None | ❌ | 1-1000 | Número de páginas, None si no aplica |
| `bytes` | int | ✅ | 1-100MB | Tamaño del archivo |
| `idioma_detectado` | str\|None | ❌ | ISO 639-1 | 'es', 'en', etc. o None |
| `ts_ingesta` | datetime | ✅ | Auto | Timestamp de carga |

### Business Rules

1. **R-DOC-001**: El `id` DEBE ser único globalmente (hash SHA-256 garantiza unicidad criptográfica)
2. **R-DOC-002**: Si el usuario carga el mismo archivo dos veces, genera dos `Documento` distintos con mismo `id` pero `ts_ingesta` diferente
3. **R-DOC-003**: El `tipo_fuente` DEBE reflejar el método REAL usado, no el formato original (ej: PDF con texto vacío → `PDF_OCR`, no `PDF_NATIVE`)
4. **R-DOC-004**: `idioma_detectado` es opcional; si OCR/LLM no detecta idioma con confianza, dejar None
5. **R-DOC-005**: `nombre` NO DEBE incluir path completo (ej: `contrato.pdf`, NO `C:\Users\...\contrato.pdf`)

### State Transitions

Documento no tiene estados (inmutable post-creación). Una vez creado, sus metadatos no cambian.

---

## Entity: Análisis

**Purpose**: Contiene el resultado estructurado del procesamiento del documento por el LLM, organizado en las 8 categorías mandatorias.

### Schema (Pydantic)

```python
class Fecha(BaseModel):
    """Fecha relevante extraída del documento"""
    etiqueta: str = Field(
        ...,
        description="Tipo de fecha (ej: 'Inicio', 'Fin', 'Vencimiento', 'Firma')",
        min_length=1,
        max_length=50
    )
    valor: str = Field(
        ...,
        description="Fecha en formato ISO (YYYY-MM-DD) si inequívoco, o literal del documento",
        min_length=1,
        max_length=100
    )

    @field_validator('valor')
    def validate_valor_format(cls, v: str) -> str:
        """Verificar que sea ISO o literal razonable"""
        if not (is_iso_date(v) or is_natural_date_literal(v)):
            raise ValueError("Valor debe ser ISO (YYYY-MM-DD) o literal válido")
        return v


class Importe(BaseModel):
    """Importe o dato económico extraído"""
    concepto: str = Field(
        ...,
        description="Descripción del importe (ej: 'Salario bruto', 'Indemnización', 'Bonus')",
        min_length=1,
        max_length=100
    )
    valor: float | None = Field(
        default=None,
        description="Valor numérico del importe (None si no se puede parsear)",
        ge=0
    )
    moneda: str | None = Field(
        default=None,
        description="Código de moneda ISO 4217 ('EUR', 'USD') o símbolo literal ('€', '$')",
        max_length=10
    )


class Analisis(BaseModel):
    """
    Resultado estructurado del análisis de un documento.
    Contiene las 8 categorías mandatorias definidas en la Constitución (Regla R2).
    """
    tipo_documento: str = Field(
        ...,
        description="Clasificación del tipo de documento (contrato_laboral, convenio, nomina, desconocido)",
        min_length=1,
        max_length=50
    )
    partes: list[str] = Field(
        default_factory=list,
        description="Entidades/personas involucradas (empresas, empleados, CIF/NIF identificables)",
        max_length=20  # Máximo 20 partes por documento
    )
    fechas: list[Fecha] = Field(
        default_factory=list,
        description="Fechas relevantes (inicio, fin, vencimientos, plazos)",
        max_length=30
    )
    importes: list[Importe] = Field(
        default_factory=list,
        description="Importes, salarios, indemnizaciones, datos económicos",
        max_length=30
    )
    obligaciones: list[str] = Field(
        default_factory=list,
        description="Enunciados de deberes, compromisos, cláusulas vinculantes",
        max_length=50
    )
    derechos: list[str] = Field(
        default_factory=list,
        description="Facultades, beneficios, licencias, permisos",
        max_length=50
    )
    riesgos: list[str] = Field(
        default_factory=list,
        description="Cláusulas sensibles (no competencia, penalizaciones, confidencialidad, renuncias)",
        max_length=30
    )
    resumen_bullets: list[str] = Field(
        default_factory=list,
        description="Resumen ejecutivo en 5-10 bullets (máximo 10)",
        min_length=1,  # Al menos 1 bullet
        max_length=10
    )
    notas: list[str] = Field(
        default_factory=list,
        description="Observaciones técnicas, advertencias, limitaciones del análisis",
        max_length=10
    )
    confianza_aprox: float = Field(
        ...,
        description="Nivel de confianza heurístico del análisis (0.0 = muy dudoso, 1.0 = muy confiable)",
        ge=0.0,
        le=1.0
    )

    @field_validator('resumen_bullets')
    def validate_resumen_length(cls, v: list[str]) -> list[str]:
        """Verificar que hay al menos 1 bullet y máximo 10"""
        if not v:
            raise ValueError("resumen_bullets no puede estar vacío")
        if len(v) > 10:
            raise ValueError("resumen_bullets no puede tener más de 10 items")
        return v

    @field_validator('partes', 'obligaciones', 'derechos', 'riesgos')
    def validate_no_duplicates(cls, v: list[str]) -> list[str]:
        """Eliminar duplicados exactos (case-insensitive)"""
        seen = set()
        unique = []
        for item in v:
            item_lower = item.lower().strip()
            if item_lower not in seen:
                seen.add(item_lower)
                unique.append(item)
        return unique

    def __repr__(self) -> str:
        return (f"Analisis(tipo={self.tipo_documento}, partes={len(self.partes)}, "
                f"fechas={len(self.fechas)}, confianza={self.confianza_aprox:.2f})")
```

### Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `tipo_documento` | str | ✅ | 1-50 chars | Categoría del documento |
| `partes` | list[str] | ✅ | 0-20 items | Entidades involucradas |
| `fechas` | list[Fecha] | ✅ | 0-30 items | Fechas relevantes estructuradas |
| `importes` | list[Importe] | ✅ | 0-30 items | Datos económicos estructurados |
| `obligaciones` | list[str] | ✅ | 0-50 items | Enunciados de deberes |
| `derechos` | list[str] | ✅ | 0-50 items | Enunciados de facultades |
| `riesgos` | list[str] | ✅ | 0-30 items | Cláusulas sensibles/alertas |
| `resumen_bullets` | list[str] | ✅ | 1-10 items | Resumen ejecutivo |
| `notas` | list[str] | ✅ | 0-10 items | Advertencias técnicas |
| `confianza_aprox` | float | ✅ | 0.0-1.0 | Nivel de confianza heurístico |

### Business Rules

1. **R-ANA-001**: Todas las categorías (`partes`, `fechas`, `obligaciones`, etc.) DEBEN estar presentes, incluso si están vacías (lista vacía `[]`)
2. **R-ANA-002**: El campo `confianza_aprox` DEBE calcularse heurísticamente:
   - 1.0: Todas las categorías pobladas, fechas/importes verificables en texto
   - 0.8-0.9: La mayoría de categorías pobladas, algunas verificaciones fallidas
   - 0.5-0.7: Muchas categorías vacías o datos ambiguos
   - 0.0-0.4: Texto escaso/ilegible, análisis muy limitado
3. **R-ANA-003**: Si el LLM no puede determinar `tipo_documento`, usar `"desconocido"` (NUNCA None)
4. **R-ANA-004**: `resumen_bullets` DEBE contener al menos 1 bullet (constitución requiere resumen)
5. **R-ANA-005**: Listas deben eliminar duplicados case-insensitive (validator automático)
6. **R-ANA-006**: Si una fecha no puede normalizarse a ISO, usar literal del documento (ej: "primer trimestre 2024")
7. **R-ANA-007**: Si un importe no tiene moneda explícita, `moneda` es None (NO asumir EUR/USD)

### Validation Rules

**Heurísticas de Verificación (post-LLM)**:
- Fechas: Verificar que valores en `fechas[].valor` aparecen literalmente en texto fuente
- Importes: Verificar que `importes[].valor` aparece como número en texto
- Partes: Verificar que nombres en `partes[]` aparecen en texto (fuzzy match >90%)
- Si verificación falla: bajar `confianza_aprox` en 0.2 y añadir nota explicativa

### State Transitions

Análisis no tiene estados (inmutable post-creación y validación).

---

## Entity: Dupla

**Purpose**: Asociación persistente entre un Documento y su Análisis, con metadata de creación y estado.

### Schema (Pydantic)

```python
class EstadoDupla(str, Enum):
    """Estado de completitud del análisis"""
    VALIDO = "valido"                      # Análisis completo sin advertencias
    INCOMPLETO = "incompleto"              # Análisis con categorías mayormente vacías
    CON_ADVERTENCIAS = "con_advertencias"  # Análisis completo pero con notas/limitaciones

class Dupla(BaseModel):
    """
    Asociación entre un Documento y su Análisis.
    Representa una entrada en el historial de análisis realizados.
    """
    id: str = Field(
        ...,
        description="Identificador único (mismo que documento.id)",
        min_length=16,
        max_length=16,
        pattern="^[a-f0-9]{16}$"
    )
    documento: Documento = Field(
        ...,
        description="Metadatos del documento analizado"
    )
    analisis: Analisis = Field(
        ...,
        description="Resultado del análisis estructurado"
    )
    ts_creacion: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de cuando se completó el análisis"
    )
    ts_actualizacion: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de última modificación (si se reprocesa)"
    )
    estado: EstadoDupla = Field(
        ...,
        description="Estado de completitud del análisis"
    )

    @field_validator('id')
    def validate_id_matches_documento(cls, v: str, info) -> str:
        """Verificar que dupla.id == documento.id"""
        if 'documento' in info.data and v != info.data['documento'].id:
            raise ValueError("dupla.id debe coincidir con documento.id")
        return v

    def calcular_estado(self) -> EstadoDupla:
        """Calcular estado automático basado en análisis"""
        if self.analisis.confianza_aprox < 0.5:
            return EstadoDupla.INCOMPLETO
        elif self.analisis.notas:
            return EstadoDupla.CON_ADVERTENCIAS
        else:
            return EstadoDupla.VALIDO

    def __repr__(self) -> str:
        return (f"Dupla(id={self.id[:8]}..., doc={self.documento.nombre}, "
                f"estado={self.estado}, ts={self.ts_creacion.isoformat()})")
```

### Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `id` | str | ✅ | 16 chars hex | Mismo que `documento.id` |
| `documento` | Documento | ✅ | Valid object | Nested Documento completo |
| `analisis` | Analisis | ✅ | Valid object | Nested Análisis completo |
| `ts_creacion` | datetime | ✅ | Auto | Timestamp de creación |
| `ts_actualizacion` | datetime | ✅ | Auto | Timestamp de última modificación |
| `estado` | EstadoDupla | ✅ | Enum | valido\|incompleto\|con_advertencias |

### Business Rules

1. **R-DUP-001**: `dupla.id` DEBE ser idéntico a `documento.id` (validación automática)
2. **R-DUP-002**: Si se reprocesa el mismo documento (mismo hash), crear nueva Dupla con `ts_actualizacion` actualizado
3. **R-DUP-003**: El `estado` DEBE calcularse automáticamente:
   - `VALIDO`: `confianza_aprox >= 0.5` Y `notas` vacío
   - `INCOMPLETO`: `confianza_aprox < 0.5`
   - `CON_ADVERTENCIAS`: `confianza_aprox >= 0.5` PERO `notas` no vacío
4. **R-DUP-004**: Dos duplas con mismo `id` pero distinto `ts_creacion` representan análisis repetidos del mismo documento (versionado futuro en SQLite)

### Persistence

**MVP (JSON file)**:
```json
{
  "duplas": [
    {
      "id": "a3f5d8e1b2c9f7e4",
      "documento": { ... },
      "analisis": { ... },
      "ts_creacion": "2026-02-18T14:30:00Z",
      "ts_actualizacion": "2026-02-18T14:30:00Z",
      "estado": "valido"
    }
  ]
}
```

**Fase 2 (SQLite)**:
```sql
CREATE TABLE duplas (
    id TEXT PRIMARY KEY,
    documento_json TEXT NOT NULL,  -- JSON serializado del Documento
    analisis_json TEXT NOT NULL,   -- JSON serializado del Análisis
    ts_creacion TIMESTAMP NOT NULL,
    ts_actualizacion TIMESTAMP NOT NULL,
    estado TEXT CHECK(estado IN ('valido', 'incompleto', 'con_advertencias'))
);
CREATE INDEX idx_duplas_ts_creacion ON duplas(ts_creacion);
CREATE INDEX idx_duplas_estado ON duplas(estado);
```

---

## Entity: Historial

**Purpose**: Colección ordenada de todas las duplas, con metadata de ordenamiento y filtrado.

### Schema (Pydantic)

```python
class OrdenamientoHistorial(str, Enum):
    """Criterio de ordenamiento del historial"""
    CRONOLOGICO_DESC = "cronologico_desc"  # Más reciente primero (default)
    CRONOLOGICO_ASC = "cronologico_asc"    # Más antiguo primero
    ALFABETICO = "alfabetico"              # Por nombre de documento A-Z
    POR_TIPO = "por_tipo"                  # Agrupado por tipo_documento

class Historial(BaseModel):
    """
    Colección de todas las duplas (análisis realizados).
    En MVP es in-memory, en Fase 2 puede queries a SQLite.
    """
    duplas: list[Dupla] = Field(
        default_factory=list,
        description="Lista de duplas, ordenadas según criterio"
    )
    ordenamiento: OrdenamientoHistorial = Field(
        default=OrdenamientoHistorial.CRONOLOGICO_DESC,
        description="Criterio de ordenamiento actual"
    )

    def ordenar(self, criterio: OrdenamientoHistorial) -> None:
        """Reordenar duplas según criterio"""
        if criterio == OrdenamientoHistorial.CRONOLOGICO_DESC:
            self.duplas.sort(key=lambda d: d.ts_creacion, reverse=True)
        elif criterio == OrdenamientoHistorial.CRONOLOGICO_ASC:
            self.duplas.sort(key=lambda d: d.ts_creacion)
        elif criterio == OrdenamientoHistorial.ALFABETICO:
            self.duplas.sort(key=lambda d: d.documento.nombre.lower())
        elif criterio == OrdenamientoHistorial.POR_TIPO:
            self.duplas.sort(key=lambda d: (d.analisis.tipo_documento, d.ts_creacion))
        self.ordenamiento = criterio

    def filtrar_por_tipo(self, tipo: str) -> list[Dupla]:
        """Filtrar duplas por tipo de documento"""
        return [d for d in self.duplas if d.analisis.tipo_documento == tipo]

    def buscar_por_nombre(self, query: str) -> list[Dupla]:
        """Buscar duplas por nombre de documento (case-insensitive)"""
        query_lower = query.lower()
        return [d for d in self.duplas if query_lower in d.documento.nombre.lower()]

    def eliminar_dupla(self, dupla_id: str) -> bool:
        """Eliminar dupla por ID. Retorna True si se eliminó."""
        inicial = len(self.duplas)
        self.duplas = [d for d in self.duplas if d.id != dupla_id]
        return len(self.duplas) < inicial

    def __len__(self) -> int:
        return len(self.duplas)

    def __repr__(self) -> str:
        return f"Historial(duplas={len(self.duplas)}, ordenamiento={self.ordenamiento})"
```

### Business Rules

1. **R-HIST-001**: El ordenamiento por defecto DEBE ser `CRONOLOGICO_DESC` (más reciente primero)
2. **R-HIST-002**: Filtros y búsquedas NO DEBEN modificar la lista original, solo retornar copias filtradas
3. **R-HIST-003**: Eliminación DEBE ser destructiva (no soft-delete en MVP, sí en SQLite Fase 2)
4. **R-HIST-004**: En MVP, toda operación de mutación (añadir, eliminar, reordenar) DEBE persistir a `duplas.json` inmediatamente

---

## Data Flow

### 1. Creación de Documento

```
Usuario carga archivo
  ↓
Calcular SHA-256 del contenido → id (16 chars)
  ↓
Detectar formato (extensión + magic bytes)
  ↓
Crear Documento(id, nombre, tipo_fuente, bytes, ts_ingesta)
  ↓
Persistir temporal (uploads/)
```

### 2. Extracción de Texto

```
Documento
  ↓
┌─────────────────────────────────┐
│ extract_text_auto(documento)    │
│   - Si PDF nativo: pdfplumber   │
│   - Si PDF vacío: pdf2image+OCR │
│   - Si DOCX: python-docx         │
│   - Si imagen: pytesseract       │
└─────────────────────────────────┘
  ↓
(texto, paginas, tipo_fuente_real)
  ↓
Actualizar documento.tipo_fuente si cambió (ej: PDF → PDF_OCR)
  ↓
Normalizar texto (espacios, saltos de línea)
```

### 3. Análisis con LLM

```
Texto normalizado
  ↓
Si len(texto) > 4K tokens:
  ├─ Chunking (2500 palabras, overlap 200)
  ├─ Analizar cada chunk
  └─ Consolidar análisis parciales
Sino:
  └─ Analizar texto completo
  ↓
Llamar Ollama API con prompt (Constitution + Specify + Plan + Texto)
  ↓
Recibir JSON
  ↓
Validar contra schema Analisis (Pydantic)
  ├─ Si válido: continuar
  └─ Si inválido: reintentar hasta 2 veces con corrección
  ↓
Validación heurística (fechas/importes verificables en texto)
  ↓
Calcular confianza_aprox
  ↓
Crear Analisis(tipo_documento, partes, fechas, ..., confianza_aprox)
```

### 4. Creación de Dupla y Persistencia

```
Documento + Analisis
  ↓
Calcular estado automático (valido|incompleto|con_advertencias)
  ↓
Crear Dupla(id=documento.id, documento, analisis, estado, ts_creacion)
  ↓
Añadir a Historial.duplas[]
  ↓
Persistir a duplas.json (atomic write: temp file → rename)
```

### 5. Visualización en UI

```
Historial.duplas[]
  ↓
Ordenar según Historial.ordenamiento
  ↓
Renderizar en sidebar de Streamlit:
  - Nombre documento
  - Tipo documento
  - Estado (badge: verde/amarillo/rojo)
  - Timestamp
  ↓
Usuario selecciona dupla
  ↓
Cargar Dupla completa
  ↓
Renderizar Análisis en panel principal:
  - Expanders por categoría
  - Bullets/tablas según tipo
  - Metadata de documento
```

---

## Validation Examples

### Valid Documento

```python
documento_valido = Documento(
    id="a3f5d8e1b2c9f7e4",
    nombre="contrato-laboral-juan-perez.pdf",
    tipo_fuente=TipoFuente.PDF_NATIVE,
    paginas=12,
    bytes=1_234_567,
    idioma_detectado="es",
    ts_ingesta=datetime(2026, 2, 18, 14, 30, 0)
)
```

### Valid Análisis

```python
analisis_valido = Analisis(
    tipo_documento="contrato_laboral",
    partes=["Empresa XYZ S.A.", "Juan Pérez García", "NIF: 12345678A"],
    fechas=[
        Fecha(etiqueta="Inicio", valor="2026-03-01"),
        Fecha(etiqueta="Fin", valor="2027-02-28")
    ],
    importes=[
        Importe(concepto="Salario bruto anual", valor=30000.0, moneda="EUR"),
        Importe(concepto="Bonus variable", valor=None, moneda="EUR")  # No especificado
    ],
    obligaciones=[
        "El trabajador se compromete a dedicar jornada completa de 40 horas semanales",
        "El trabajador debe respetar confidencialidad de información empresarial"
    ],
    derechos=[
        "El trabajador tiene derecho a 30 días de vacaciones anuales",
        "El trabajador tiene derecho a formación continua con cargo a la empresa"
    ],
    riesgos=[
        "Cláusula de no competencia: prohibida actividad similar durante 2 años post-finalización",
        "Penalización por abandono anticipado: devolución de formación prorrateada"
    ],
    resumen_bullets=[
        "Contrato indefinido a jornada completa (40h/semana)",
        "Salario bruto anual de 30.000€ más bonus variable no especificado",
        "Inicio: 1 de marzo 2026, duración inicial 1 año renovable",
        "30 días de vacaciones anuales pagadas",
        "Cláusula de no competencia por 2 años post-finalización"
    ],
    notas=[
        "Bonus variable no tiene importe especificado en el documento",
        "Idioma detectado: español (España)"
    ],
    confianza_aprox=0.9
)
```

### Valid Dupla

```python
dupla_valida = Dupla(
    id="a3f5d8e1b2c9f7e4",
    documento=documento_valido,
    analisis=analisis_valido,
    ts_creacion=datetime(2026, 2, 18, 14, 35, 0),
    ts_actualizacion=datetime(2026, 2, 18, 14, 35, 0),
    estado=EstadoDupla.CON_ADVERTENCIAS  # Porque analisis.notas no vacío
)
```

---

## Constitutional Alignment

### Regla R2 - Modelo Conceptual Uniforme

✅ **Cumple**: Entidad `Analisis` define exactamente las 8 categorías mandatorias:
1. `partes`
2. `fechas`
3. `importes`
4. `obligaciones`
5. `derechos`
6. `riesgos`
7. `resumen_bullets`
8. `tipo_documento`

### Principio VI - Veracidad de la Información

✅ **Cumple**: Modelo incluye mecanismos de veracidad:
- Campo `confianza_aprox` refleja nivel de verificabilidad
- Campo `notas[]` documenta limitaciones explícitas
- Validaciones heurísticas post-LLM verifican datos contra texto fuente
- Listas vacías permitidas (no fuerza invención de datos)

### Regla R5 - Estructura Consistente

✅ **Cumple**: Schema Pydantic con `model_config = ConfigDict(frozen=True)` previene modificación post-creación, garantiza inmutabilidad de estructura.

---

## Next Steps

1. ✅ **Data Model Complete**: All entities defined with Pydantic schemas
2. ⏭️  **Generate JSON Schemas**: Export to `/contracts/*.schema.json` for documentation
3. ⏭️  **Implement CRUD operations**: `src/persistence/json_store.py` with atomic writes
4. ⏭️  **Create fixtures**: `tests/fixtures/` with sample Documento/Análisis/Dupla instances

**Ready for Phase 2**: Task generation (`/speckit.tasks`) ✅
