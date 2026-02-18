# Implementation Plan: Analizador de Documentos Legales

**Branch**: `001-doc-analyzer` | **Date**: 2026-02-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-doc-analyzer/spec.md`

## Summary

Sistema de análisis local de documentos legales, laborales y administrativos que extrae puntos clave mediante IA local (Ollama), procesando PDF (nativos y escaneados), DOCX e imágenes con OCR. Presenta resultados estructurados en 8 categorías (partes, fechas, importes, obligaciones, derechos, riesgos, resumen, tipo), mantiene historial persistente de duplas (documento ↔ análisis) y exporta resultados en JSON, todo ejecutándose 100% offline con privacidad garantizada.

**Technical Approach**: Aplicación web local con Streamlit (Python 3.10+), extracción de texto mediante pdfplumber/python-docx/pytesseract (OCR 300 DPI), análisis por LLM local Ollama (llama3.2:3b), validación de schema con Pydantic, persistencia JSON (duplas.json), y pipeline con chunking para documentos largos + consolidación inteligente de resultados.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**:
- **UI Framework**: Streamlit 1.30+ (aplicación web local, sin servidor externo)
- **Text Extraction**:
  - `pdfplumber 0.10+` (PDF nativos con texto embebido)
  - `python-docx 1.1+` (archivos DOCX)
  - `pdf2image 1.16+` + `pytesseract 0.3.10+` (OCR para PDFs escaneados e imágenes, render 300 DPI, lang "spa" + "spa+eng")
- **AI Local**: Ollama (servicio local HTTP, puerto 11434) con modelo `llama3.2:3b` (preferente, 2GB VRAM) | Alternativas: `phi3:mini` (1GB VRAM) o `mistral:7b` (5GB VRAM)
- **Data Validation**: Pydantic 2.5+ (schemas para Documento/Análisis/Dupla, validación JSON)
- **Utilities**: `hashlib` (SHA-256 para IDs), `pillow` (mejora de imágenes pre-OCR)

**Storage**: Archivo JSON local (`duplas.json` en directorio del proyecto) | Futura migración a SQLite para versiones y queries complejas

**Testing**: pytest 7.4+ con fixtures para:
- Mocks de Ollama (responses JSON simulados)
- Documentos de prueba (PDF nativo, PDF escaneado, DOCX, imágenes)
- Validación de schemas Pydantic
- Tests de integración end-to-end (carga → extracción → análisis → persistencia)

**Target Platform**:
- **OS**: Windows 10+, macOS 12+, Linux (Ubuntu 20.04+)
- **Hardware Mínimo**: 4GB RAM, CPU dual-core (últimos 5 años), 2GB almacenamiento
- **Hardware Recomendado**: 8GB RAM, CPU quad-core, 4GB almacenamiento, GPU opcional (acelera Ollama)
- **Software Prereqs**: Tesseract OCR instalado en sistema, Ollama service ejecutándose localmente

**Project Type**: Single project (aplicación standalone Python con UI web local vía Streamlit)

**Performance Goals**:
- PDF nativo (10-20 páginas): análisis completo en <30 segundos
- PDF escaneado (5-10 páginas): OCR + análisis en <60 segundos
- Procesamiento batch de 5 documentos: <5 minutos total
- Respuesta de UI (navegación historial): <1 segundo
- Validación JSON del LLM: >85% éxito al primer intento

**Constraints**:
- **Privacidad absoluta**: 0% transmisión de datos fuera del equipo sin consentimiento explícito (Principio I - Constitución)
- **Veracidad obligatoria**: 100% del contenido del análisis debe ser verificable contra documento fuente (Principio VI - Constitución)
- **Estructura inmutable**: 8 categorías en orden fijo para todos los documentos (Regla R2 - Constitución)
- **Límite de tamaño de archivo**: 100MB máximo por documento (restricción práctica de memoria)
- **Context window del LLM**: ~4000 tokens (llama3.2:3b) → requiere chunking para docs >10 páginas
- **Temperatura del LLM**: 0.1-0.3 (determinismo alto, reducir variabilidad)
- **Sin conexión internet**: Core features deben funcionar offline (Ollama local, OCR local, persistencia local)

**Scale/Scope**:
- Historial: hasta 1000 duplas (análisis) almacenadas localmente
- Documentos: 1-100 páginas (98% de casos), soporta hasta 500 páginas con chunking
- Usuarios: single-user local (no multi-tenancy)
- Idiomas: español (primario), inglés (secundario), detección automática de idioma

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principio I - Privacidad y Operación Local

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ Ollama ejecuta localmente (no Claude API, OpenAI API ni servicios cloud)
- ✅ OCR via pytesseract (biblioteca local, no Google Vision API ni AWS Textract)
- ✅ Extracción de texto con bibliotecas Python puras (pdfplumber, python-docx)
- ✅ Almacenamiento en archivo JSON local (`duplas.json`) sin sincronización cloud
- ✅ Streamlit en modo local (no Streamlit Cloud deployment)
- ✅ Sin telemetría ni analytics externos

**Implicaciones en Arquitectura**:
- Documentar en quickstart.md cómo instalar Ollama localmente
- Incluir health check en UI para verificar que Ollama está ejecutando en `localhost:11434`
- Mostrar badge "🔒 100% Local" en UI para reforzar confianza
- Implementar flag de configuración para deshabilitar cualquier futura feature que requiera red

**Riesgos Mitigados**:
- No hay riesgo de filtración de documentos sensibles a servicios externos
- Usuario mantiene control absoluto de datos en su filesystem

### ✅ Principio II - Carga y Visualización Múltiple

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ Streamlit `file_uploader` con parámetro `accept_multiple_files=True`
- ✅ Pipeline procesa lista de archivos en secuencia (batch processing)
- ✅ Historial lateral tipo sidebar muestra todas las duplas con metadata individual
- ✅ Cada análisis mantiene estructura independiente (no hay merge involuntario)

**Implementación**:
- US3 (Carga Múltiple) implementa este principio directamente
- UI con indicador de progreso: "Procesando 3 de 5 documentos..."

### ✅ Principio III - Interfaz Clara y Directa

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ Cada dupla en historial incluye `documento.nombre` + `analisis.tipo_documento` como título
- ✅ Click en dupla → recupera análisis exacto sin ambigüedad (match por `dupla.id`)
- ✅ UI muestra metadata de trazabilidad: "Analizado el 2026-02-18 14:30 | 12 páginas | PDF OCR"

**Implementación**:
- Sidebar de Streamlit con lista de duplas (st.selectbox o custom component)
- Panel principal muestra análisis seleccionado con referencia explícita al documento origen

### ✅ Principio IV - Resultados Estructurados

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ Esquema Pydantic valida las 8 categorías obligatorias
- ✅ UI usa expanders/cards de Streamlit para separar visualmente cada categoría
- ✅ Listas con bullets (st.markdown) para obligaciones, derechos, riesgos, resumen
- ✅ Fechas e importes en formato tabular (st.dataframe o st.table)

**Implementación**:
- Template de presentación en Streamlit con secciones colapsables
- Evitar texto plano sin formato → usar componentes estructurados

### ✅ Principio V - Independencia de Formato

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ `extract_text_auto(path)` detecta formato y delega a extractor apropiado
- ✅ Normalización de texto común post-extracción (espacios, saltos de línea)
- ✅ Pipeline de análisis recibe texto plano sin conocer formato origen
- ✅ Metadata `documento.tipo_fuente` registra origen pero no afecta análisis

**Implementación**:
```python
def extract_text_auto(file_path: Path) -> tuple[str, int, str]:
    """Detecta formato y extrae texto normalizado"""
    if file_path.suffix.lower() == '.pdf':
        # Intenta pdfplumber → si falla/vacío, aplica OCR
    elif file_path.suffix.lower() in ['.docx', '.doc']:
        # python-docx
    elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff']:
        # pytesseract directo
    # Normalización común para todos
    return (texto, paginas, tipo_fuente)
```

### ✅ Principio VI - Veracidad de la Información

**Status**: ✅ **CUMPLE** con **Mitigaciones Críticas**

**Validación**:
- ✅ LLM_CONSTITUTION prompt incluye: "No inventes datos. Extrae únicamente información presente en el texto."
- ✅ Validación heurística post-análisis: verificar que fechas/números del JSON aparecen en texto fuente
- ✅ Campo `analisis.confianza_aprox` refleja nivel de verificabilidad (0.0-1.0)
- ✅ Campo `analisis.notas[]` documenta limitaciones explícitas ("Texto escaso", "OCR de baja calidad")
- ✅ Categorías vacías se devuelven como `[]` o `null`, no con placeholders inventados

**Mitigaciones Críticas**:
1. **Temperatura baja (0.1-0.3)** → reduce creatividad del LLM, aumenta reproducibilidad
2. **Reintentos con corrección** → si JSON inválido, pedir corrección sin inventar
3. **Schema estricto Pydantic** → campos tipados, no permite free-form text que invite a especulación
4. **Logging de prompts** → permitir auditoría de qué se envió al LLM vs qué devolvió

**Riesgos Residuales**:
- **Riesgo**: LLM local puede alucinar nombres de entidades similares pero no exactos
  - **Mitigación**: Validación fuzzy string matching: si `partes[0]` no aparece literal en texto, bajar `confianza_aprox` y añadir nota
- **Riesgo**: Interpretación de importes ambiguos ("hasta 5000€" → ¿5000 o rango?)
  - **Mitigación**: Preferir literals cuando hay ambigüedad, usar `notas` para aclarar contexto

**Testing**:
- Test case con documento inventado → verificar que análisis no añade información ausente
- Test case con documento ambiguo → verificar que `notas` reconoce limitación

### ✅ Principio VII - Historial y Gestión

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ `duplas.json` persiste tras cada análisis exitoso
- ✅ UI sidebar muestra lista completa de duplas con ordenamiento configurable
- ✅ Operación de eliminación con confirmación (st.button + st.warning)
- ✅ Exportación de historial completo (JSON) para backup

**Implementación**:
- US2 (Historial de Duplas) implementa este principio directamente
- CRUD operations: Create (análisis nuevo), Read (seleccionar dupla), Delete (con confirmación)
- Futura extensión: filtrado por tipo de documento, búsqueda por partes/fechas

### ✅ Principio VIII - Experiencia del Usuario

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ Flujo de 3 pasos: (1) Cargar documento(s) → (2) Ver análisis → (3) Gestionar historial
- ✅ Streamlit proporciona UI intuitiva sin terminología técnica ("Cargar Documento" no "Upload File to Buffer")
- ✅ Defaults razonables: OCR a 300 DPI (no requiere configuración), idioma español por defecto
- ✅ Indicadores de progreso con mensajes claros: "Extrayendo texto..." no "Parsing PDF stream objects"

**Anti-patterns Evitados**:
- ❌ No mostrar logs técnicos en UI (JSON raw, stack traces → solo en console/logs)
- ❌ No requerir configuración de Ollama model path (auto-detect localhost:11434)
- ❌ No pedir al usuario elegir entre "pdfplumber vs pymupdf" (auto-detect mejor opción)

**Implementación**:
- Streamlit config (`config.toml`) con tema limpio y profesional
- Mensajes de error user-friendly: "No se pudo leer el archivo PDF. Verifica que no esté protegido con contraseña." en lugar de "PyPDF2.errors.PdfReadError: EOF marker not found"

### ✅ Principio IX - Extensibilidad

**Status**: ✅ **CUMPLE**

**Validación**:
- ✅ Arquitectura en capas (UI, Extracción, Orquestación, Datos) permite reemplazar componentes
- ✅ Futuro soporte de nuevos formatos (RTF, TXT) requiere solo añadir handler en `extract_text_auto`
- ✅ Migración a SQLite planificada sin romper `duplas.json` existente (read-compatibility)
- ✅ Nuevas categorías de análisis requieren solo actualizar schema Pydantic + prompt LLM

**Extensiones Futuras Compatibles**:
- Añadir análisis comparativo (diff entre 2 duplas) sin afectar análisis individual
- Integración con servicios opcionales de traducción (opt-in, no obligatorio)
- Plugin system para extractores custom (ej: SAP PDFs con formato propietario)

**Constraints para Extensiones**:
- Toda extensión DEBE pasar Constitution Check (re-validar Principio I Privacidad)
- Nuevas features DEBEN ser opt-in si introducen dependencias externas

---

### ⚠️  Constitutional Compliance Summary

**Overall Status**: ✅ **TODOS LOS PRINCIPIOS CUMPLIDOS**

**Violations**: 0 (cero violaciones)

**Justifications Required**: N/A

**Re-Check After Phase 1**: ✅ Mandatory (verificar que data-model.md y contracts/ mantienen alineación)

## Project Structure

### Documentation (this feature)

```text
specs/001-doc-analyzer/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0: Technology research & decisions
├── data-model.md        # Phase 1: Entidades Documento/Análisis/Dupla
├── quickstart.md        # Phase 1: Guía de instalación y primeros pasos
├── contracts/           # Phase 1: Schemas (Pydantic models, JSON examples)
│   ├── documento.schema.json
│   ├── analisis.schema.json
│   ├── dupla.schema.json
│   └── ollama-prompt.md
├── checklists/
│   └── requirements.md  # Spec validation (completed)
└── tasks.md             # Phase 2: Task list (generated by /speckit.tasks)
```

### Source Code (repository root)

```text
# Single Project Structure (Python)
src/
├── models/                      # Entidades y schemas Pydantic
│   ├── __init__.py
│   ├── documento.py             # Clase Documento + schema
│   ├── analisis.py              # Clase Analisis + schema
│   └── dupla.py                 # Clase Dupla + schema
├── extractors/                  # Capa de extracción de texto
│   ├── __init__.py
│   ├── base.py                  # Abstract BaseExtractor
│   ├── pdf_native.py            # pdfplumber para PDFs nativos
│   ├── pdf_ocr.py               # pdf2image + pytesseract para escaneados
│   ├── docx_extractor.py        # python-docx para DOCX
│   └── image_extractor.py       # pytesseract directo para imágenes
├── orchestration/               # Capa de orquestación de análisis
│   ├── __init__.py
│   ├── analyzer.py              # Pipeline principal: extracción → análisis → validación
│   ├── ollama_client.py         # Cliente HTTP para Ollama API
│   ├── prompt_builder.py        # Ensambla prompts (Constitution + Specify + Plan + Texto)
│   ├── json_validator.py        # Validación de JSON contra schemas, reintentos
│   └── chunker.py               # Chunking para documentos largos + consolidación
├── persistence/                 # Capa de datos y almacenamiento
│   ├── __init__.py
│   ├── json_store.py            # CRUD operations sobre duplas.json
│   └── sqlite_store.py          # (Futuro) Migración a SQLite
├── ui/                          # Capa de interfaz Streamlit
│   ├── __init__.py
│   ├── app.py                   # Entry point de Streamlit (st.run)
│   ├── components/
│   │   ├── file_uploader.py     # Componente de carga múltiple
│   │   ├── analysis_view.py     # Tarjetas/bullets por categorías
│   │   ├── history_sidebar.py   # Lista de duplas en sidebar
│   │   └── export_buttons.py    # Controles de exportación
│   └── pages/                   # (Opcional) Multi-page app
│       ├── main.py              # Página principal
│       └── settings.py          # Configuración (OCR DPI, modelo Ollama)
└── utils/                       # Utilidades transversales
    ├── __init__.py
    ├── hashing.py               # SHA-256 para IDs de documento
    ├── logging_config.py        # Setup de logging
    ├── text_normalizer.py       # Normalización de texto post-extracción
    └── validators.py            # Validaciones heurísticas (fechas, importes)

tests/
├── unit/                        # Tests de unidad por módulo
│   ├── test_extractors.py      # Mock PDFs/DOCX/imágenes
│   ├── test_analyzer.py         # Mock Ollama responses
│   ├── test_json_validator.py   # Casos de JSONs válidos/inválidos
│   └── test_chunker.py          # Tests de chunking + consolidación
├── integration/                 # Tests end-to-end
│   ├── test_pipeline.py         # Carga → Extracción → Análisis → Persistencia
│   └── test_ui.py               # (Opcional) Selenium/Playwright para UI
├── fixtures/                    # Documentos de prueba
│   ├── contrato_laboral.pdf     # PDF nativo (10 páginas)
│   ├── nomina_escaneada.pdf     # PDF escaneado (2 páginas)
│   ├── convenio.docx            # DOCX (5 páginas)
│   └── recibo_imagen.png        # Imagen de recibo
└── conftest.py                  # Fixtures de pytest (mocks Ollama, temp dirs)

data/                            # Almacenamiento local de datos
├── duplas.json                  # Historial de análisis (MVP)
├── uploads/                     # Temporal para archivos cargados
└── cache/                       # (Opcional) Cache de OCR para re-procesamiento rápido

config/                          # Configuración de aplicación
├── ollama_config.yaml           # Endpoints, modelos, temperatura
├── streamlit_config.toml        # Tema y configuración de Streamlit
└── logging.yaml                 # Niveles de log por módulo

docs/                            # Documentación técnica adicional
├── architecture.md              # Diagrama de capas y flujo de datos
├── prompts.md                   # Documentación detallada de prompts del LLM
└── deployment.md                # Guía de instalación de prereqs (Ollama, Tesseract)

requirements.txt                 # Dependencias Python (pip)
pyproject.toml                   # Configuración de proyecto (Poetry/PDM opcional)
.gitignore                       # Excluir data/, uploads/, cache/
README.md                        # Overview del proyecto y quickstart
```

**Structure Decision**:
Seleccionada **Opción 1 - Single Project** porque:
- No hay frontend/backend separados (Streamlit embebe UI en mismo proceso Python)
- No hay API REST externa (Ollama es dependency local, no servicio propio)
- Arquitectura monolítica simplifica deployment (un solo comando `streamlit run`)
- Capas lógicas separadas en directorios (`models/`, `extractors/`, `orchestration/`, `ui/`) mantienen modularidad sin overhead de microservicios

Estructura permite migración futura a arquitectura web (FastAPI backend + React frontend) si se requiere multi-usuario o deployment cloud, pero MVP prioriza simplicidad de single-user local.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**N/A** - No hay violaciones constitucionales que requieran justificación.

Todas las decisiones técnicas (Ollama local, pytesseract, JSON storage, Streamlit local) están alineadas con los 9 principios inmutables de la constitución, especialmente Principio I (Privacidad Local) y Principio VI (Veracidad de la Información).

---

## Phase 0: Research & Decisions

*Output: `research.md` documenting technology choices and rationale*

**Research Completed**: ✅ (decisions provided by user, documented below)

### Decision 1: Language & Framework - Python 3.10+ con Streamlit

**Rationale**:
- **Python**: Ecosistema maduro para ML/NLP (Ollama Python SDK), procesamiento de documentos (pdfplumber, python-docx), OCR (pytesseract bindings)
- **Streamlit**: Framework rápido para prototipos de ML apps, requiere mínimo código para UI compleja, soporta components interactivos (file uploader, sidebar, expanders), deployment local trivial (`streamlit run app.py`)
- **Alternativas consideradas**:
  - Flask/FastAPI + HTML/JS: Mayor control pero 3-5x más código, overhead innecesario para single-user local
  - Jupyter Notebook: No apto para end-users no técnicos, falta UI production-ready
  - Electron + Python: Complejidad de empaquetado, overhead de Chromium

**Best Practices**:
- Usar virtual environments (venv/conda) para aislar dependencias
- Pin versions en requirements.txt para reproducibilidad
- Streamlit session_state para persistencia de estado entre reruns

### Decision 2: Text Extraction - pdfplumber + python-docx + pytesseract

**Rationale**:
- **pdfplumber** (PDFs nativos): Mejor balance extracción/layout, soporta tablas, open-source
  - Alternativas: PyPDF2 (básico), pymupdf (rápido pero licencia AGPL), pdfminer (complejo)
- **python-docx** (DOCX): Estándar de facto, soporta estilos y tablas, activamente mantenido
  - Alternativas: docx2txt (solo texto plano, pierde estructura)
- **pytesseract + pdf2image** (OCR):
  - Tesseract: Open-source maduro (Google), soporta 100+ idiomas incluido español, detección automática de layout
  - pdf2image: Convierte PDF pages a imágenes para OCR (usa poppler internamente)
  - **300 DPI**: Balance calidad/velocidad (200 DPI = rápido pero inexacto, 400 DPI = lento pero preciso)
  - **"spa" + "spa+eng"**: Español primario, fallback a multilenguaje para documentos híbridos
  - Alternativas cloud descartadas: Google Vision API (viola Principio I), AWS Textract (pago + cloud)

**Best Practices**:
- Pre-procesamiento de imágenes: binarización, deskew, noise reduction (Pillow)
- Detección automática de texto en PDF antes de OCR (evitar OCR innecesario)
- Chunking de PDFs grandes: 1 página a la vez para OCR (gestión de memoria)

### Decision 3: LLM Local - Ollama con llama3.2:3b

**Rationale**:
- **Ollama**: Servicio local HTTP que gestiona modelos LLM, fácil instalación (single binary), API REST simple, soporta streaming, GPU acceleration opcional
  - Alternativas: llama.cpp (más control pero requiere compilación), Hugging Face Transformers (complejo, overhead de dependencies)
- **llama3.2:3b**:
  - **Pros**: Equilibrio calidad/recursos (2GB VRAM), buen seguimiento de instrucciones JSON, context window 4K tokens, inference ~2-5 sec/respuesta en CPU
  - **Cons**: Puede alucinar con documentos ambiguos (mitigar con temperatura baja + validación)
- **Alternativas**:
  - **phi3:mini** (1GB): Más ligero, bueno para HW limitado, menor calidad de extracción de entidades complejas
  - **mistral:7b** (5GB): Mejor calidad, requiere 8GB+ RAM, inference más lenta (5-10 sec)
  - **GPT-4/Claude API**: Descartados por violar Principio I (cloud) y costo por uso

**Best Practices**:
- Temperatura 0.1-0.3 para tareas de extracción (reduce creatividad)
- System prompt robusto con ejemplos few-shot (mejora adherencia a schema JSON)
- Timeouts generosos (30-60 seg) para inference en CPU
- Reintentos con backoff exponencial si Ollama no responde

### Decision 4: Data Validation - Pydantic 2.5+

**Rationale**:
- **Pydantic**: Validación de schemas Python con typing nativo, serialización/deserialización JSON automática, mensajes de error claros
  - Alternativas: marshmallow (menos type-safe), dataclasses + manual validation (más código)
- **Use cases**:
  - Definir schemas de Documento/Análisis/Dupla con tipos estrictos
  - Validar JSON del LLM contra schema antes de persistir
  - Auto-generar JSON Schema para documentación (contracts/)

**Best Practices**:
- Usar `Field(..., description="...")` para documentar campos
- Validators custom para lógica compleja (ej: verificar que fechas están en formato ISO o literal)
- Strict mode para rechazar campos extra del LLM

### Decision 5: Persistence - JSON file (duplas.json) → SQLite (fase 2)

**Rationale**:
- **MVP (JSON file)**:
  - **Pros**: Zero setup, human-readable, fácil backup (copy file), compatible con git
  - **Cons**: Performance degrada con >1000 duplas, no soporta queries complejas, riesgo de corrupción con escrituras concurrentes
  - **Uso**: Historial lineal, CRUD simple, exportación directa
- **Fase 2 (SQLite)**:
  - **Pros**: Queries rápidas (filtrar por tipo_documento, fechas), transacciones ACID, soporta versiones de análisis, schema migrations
  - **Cons**: Requiere schema design, más complejo de debug
  - **Migración**: Script de import de duplas.json → SQLite (preservar backward compatibility)

**Best Practices**:
- JSON: atomic writes (write to temp file → rename), validation antes de guardar
- SQLite: usar ORM ligero (SQLModel = Pydantic + SQLAlchemy) para mantener consistency con schemas Pydantic

### Decision 6: Chunking Strategy - Sliding window con consolidación inteligente

**Rationale**:
- **Problema**: llama3.2:3b tiene context window de ~4K tokens (~3000 palabras). Documentos de 20+ páginas exceden límite.
- **Solución**:
  1. **Chunking**: Dividir texto en chunks de ~2500 palabras con overlap de 200 palabras (preserva contexto en fronteras)
  2. **Análisis por chunk**: Cada chunk genera JSON parcial
  3. **Consolidación**: Merge de listas (partes, fechas, obligaciones), deduplicación fuzzy (similaridad >90%), reconciliación de conflictos (conservar todos los valores + nota en `analisis.notas`)
  4. **Recorte final**: `resumen_bullets` limitado a 10 items (priorizar bullets más densos en keywords)

**Alternativas consideradas**:
- Map-Reduce: Chunk → summarize → re-analyze summaries (pierde detalles, 2 pasadas de LLM)
- Embeddings + RAG: Over-engineering para MVP, requiere vector DB

**Best Practices**:
- Chunking respeta fronteras de párrafos (no cortar frases)
- Deduplicación de fechas/importes por valor exacto
- Consolidación de partes por similitud de nombres (Levenshtein distance)

---

*See [research.md](./research.md) for detailed investigation and trade-offs*

## Phase 1: Design & Contracts

*Output: `data-model.md`, `/contracts/*.schema.json`, `quickstart.md`*

### Data Model Summary

**Core Entities** (see [data-model.md](./data-model.md) for full schemas):

1. **Documento** (archivo cargado):
   - `id: str` (SHA-256 truncado a 16 chars)
   - `nombre: str` (filename original)
   - `tipo_fuente: Literal["pdf_native", "pdf_ocr", "docx", "image", "txt"]`
   - `paginas: int | None`, `bytes: int`, `idioma_detectado: str | None`
   - `ts_ingesta: datetime`

2. **Análisis** (resultado del LLM):
   - `tipo_documento: str` (contrato_laboral | convenio | nomina | desconocido)
   - `partes: list[str]` (entidades/denominaciones)
   - `fechas: list[Fecha]` donde `Fecha = {etiqueta: str, valor: str}`
   - `importes: list[Importe]` donde `Importe = {concepto: str, valor: float | None, moneda: str | None}`
   - `obligaciones: list[str]`, `derechos: list[str]`, `riesgos: list[str]`
   - `resumen_bullets: list[str]` (5-10 items)
   - `notas: list[str]` (advertencias, limitaciones)
   - `confianza_aprox: float` (0.0-1.0, heurística de verificabilidad)

3. **Dupla** (asociación persistente):
   - `id: str` (mismo que `documento.id`)
   - `documento: Documento`
   - `analisis: Analisis`
   - `ts_creacion: datetime`, `ts_actualizacion: datetime`
   - `estado: Literal["valido", "incompleto", "con_advertencias"]`

**Relationships**:
- Dupla 1:1 Documento (una dupla por documento por ejecución)
- Dupla 1:1 Análisis (un análisis por dupla)
- Historial 1:N Duplas (lista de duplas ordenadas cronológicamente)

### Contract Artifacts

**Files in `/contracts/`** (see [contracts/](./contracts/) directory):

1. `documento.schema.json` - JSON Schema de Documento (Pydantic model export)
2. `analisis.schema.json` - JSON Schema de Análisis (validación de response del LLM)
3. `dupla.schema.json` - JSON Schema de Dupla completa
4. `ollama-prompt.md` - Documentación de prompts (Constitution, Specify, Plan) con ejemplos
5. `example-request.json` - Request HTTP a Ollama (POST /api/generate)
6. `example-response.json` - Response válido del LLM con análisis completo

**API Contract - Ollama HTTP**:
```
Endpoint: POST http://localhost:11434/api/generate
Headers: {"Content-Type": "application/json"}
Body: {
  "model": "llama3.2:3b",
  "prompt": "{CONSTITUTION + SPECIFY + PLAN + DOCUMENTO}",
  "temperature": 0.2,
  "stream": false,
  "format": "json"
}
Response: {
  "response": "{json_string_con_analisis}",
  "done": true
}
```

### Quickstart Guide

**User-facing quick-start** (see [quickstart.md](./quickstart.md)):

1. **Prerrequisitos**:
   - Python 3.10+ instalado
   - Tesseract OCR instalado (`brew install tesseract` macOS, `apt install tesseract-ocr` Linux, [installer](https://github.com/UB-Mannheim/tesseract/wiki) Windows)
   - Ollama instalado y ejecutando ([ollama.com](https://ollama.com))

2. **Instalación**:
   ```bash
   git clone <repo>
   cd <repo>
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ollama pull llama3.2:3b
   ```

3. **Ejecución**:
   ```bash
   streamlit run src/ui/app.py
   ```
   Abre navegador en http://localhost:8501

4. **Uso básico**:
   - Cargar documento(s) con botón "Seleccionar archivos"
   - Esperar análisis (indicador de progreso)
   - Ver resultados en tarjetas por categoría
   - Navegar historial en barra lateral
   - Exportar con botón "Exportar JSON"

---

### Agent Context Update

**Action**: Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`

**Expected Changes**:
- Add Python 3.10+, Streamlit, Ollama to technology stack
- Add pdfplumber, python-docx, pytesseract to dependencies
- Preserve manual additions between markers

*Note: This step will be executed automatically at end of Phase 1*

---

## Constitutional Re-Check (Post-Design)

*GATE: Verify all design decisions maintain constitutional compliance*

### Re-validation Results

✅ **Principio I (Privacidad)**: Data model no incluye campos de sincronización cloud, schemas no requieren tokens de API externa

✅ **Principio VI (Veracidad)**: Campo `confianza_aprox` + `notas[]` permite transparencia sobre limitaciones, schema no permite campos ambiguos

✅ **Regla R2 (8 categorías)**: Schema `Analisis` define exactamente las 8 categorías obligatorias como campos requeridos

✅ **Regla R5 (Estructura inmutable)**: Schema Pydantic con `frozen=True` previene modificación post-creación

**Status**: ✅ **ALL GATES PASSED** - Proceed to Phase 2 (Task Generation)

---

## Next Steps

1. ✅ **Phase 0 & 1 Complete**: research.md, data-model.md, contracts/, quickstart.md generated
2. ⏭️  **Phase 2**: Run `/speckit.tasks` to generate dependency-ordered task list (tasks.md)
3. ⏭️  **Phase 3**: Run `/speckit.implement` to execute tasks with validation

**Artifacts Ready for Development**:
- [spec.md](./spec.md) - Business requirements (WHAT & WHY)
- [plan.md](./plan.md) - Technical implementation (HOW)
- [research.md](./research.md) - Technology decisions & rationale
- [data-model.md](./data-model.md) - Entity schemas & relationships
- [contracts/](./contracts/) - API schemas & examples
- [quickstart.md](./quickstart.md) - Installation & usage guide

**Estimated Development Time**: 6-7 days (see Hitos H1-H4 in user input)

**Ready to proceed with `/speckit.tasks`** ✅
