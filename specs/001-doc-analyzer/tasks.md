# Tasks: Analizador de Documentos Legales

**Input**: Design documents from `/specs/001-doc-analyzer/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT explicitly requested in specification - focus on implementation and validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and environment preparation

- [X] T001 Create project structure per implementation plan with directories: `src/models/`, `src/extractors/`, `src/orchestration/`, `src/persistence/`, `src/ui/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `data/`, `config/`, `docs/`
  - **DoD**: Estructura de carpetas creada, README.md con overview del proyecto, LICENSE (si aplica), repositorio inicializado con git

- [X] T002 Create `requirements.txt` with dependencies: streamlit>=1.30, pdfplumber>=0.10, python-docx>=1.1, pillow, pdf2image>=1.16, pytesseract>=0.3.10, requests, pydantic>=2.5, pytest>=7.4
  - **DoD**: Instalación local exitosa con `pip install -r requirements.txt`, venv activado sin errores

- [X] T003 [P] Document Tesseract and Poppler installation in docs/deployment.md with instructions for macOS (brew install tesseract poppler), Windows (installer links), Linux (apt install tesseract-ocr poppler-utils)
  - **DoD**: Guía con comandos y rutas PATH por sistema operativo, verificación local con `tesseract --version` exitosa

- [X] T004 [P] Document Ollama installation and model setup in docs/deployment.md with instructions for downloading Ollama and pulling llama3.2:3b model
  - **DoD**: Prompt de prueba local exitoso contra `http://localhost:11434`, health check documentado

- [X] T005 [P] Create configuration files in `config/`: `ollama_config.yaml` (endpoint, modelo, temperatura), `streamlit_config.toml` (tema UI), `logging.yaml` (niveles de log por módulo)
  - **DoD**: Módulo de carga de configuración en `src/utils/config_loader.py` con valores por defecto seguros, validación de campos obligatorios

**Checkpoint**: Project structure ready - can proceed to foundational models

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and schemas that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Define Pydantic schema for `Analisis` in `src/models/analisis.py` with 8 mandatory fields: tipo_documento, partes (list), fechas (list of {etiqueta, valor}), importes (list of {concepto, valor, moneda}), obligaciones (list), derechos (list), riesgos (list), resumen_bullets (list), notas (list), confianza_aprox (float 0.0-1.0)
  - **DoD**: Clase `Analisis` valida datos con defaults vacíos para listas, validación de confianza_aprox en rango [0.0, 1.0], exports to_dict() method

- [X] T007 [P] Define Pydantic schemas for `Documento` and `Dupla` in `src/models/documento.py` and `src/models/dupla.py`
  - **DoD**: `Documento` con campos id (str 16 chars), nombre, tipo_fuente (enum), paginas (int|None), bytes (int|None), idioma_detectado (str|None), ts_ingesta (datetime). `Dupla` con id, documento (Documento), analisis (Analisis), ts_creacion, ts_actualizacion, estado (enum: valido|incompleto|con_advertencias)

- [X] T008 Implement JSON serialization/deserialization utilities in `src/utils/serialization.py` with functions `to_json(obj: BaseModel) -> str` and `from_json(cls: Type[BaseModel], data: str) -> BaseModel`
  - **DoD**: Round-trip tests pass: object → JSON → object preserva todos los campos, manejo de datetime en formato ISO 8601

- [X] T009 Implement document metadata computation in `src/utils/hashing.py` with function `compute_doc_meta(file_path: Path) -> dict` returning {id: SHA-256 hash (16 chars), bytes: file size, paginas: page count if applicable}
  - **DoD**: Función retorna ID único estable (mismo archivo = mismo hash), conteo de páginas correcto para PDF/DOCX

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Análisis Individual de Documento (Priority: P1) 🎯 MVP

**Goal**: Usuario carga un único documento (PDF/DOCX/imagen), sistema extrae texto, genera análisis estructurado en 8 categorías y presenta resultados visualmente

**Independent Test**: Cargar un PDF nativo, verificar que se genera y muestra análisis con las 8 categorías (con "No disponible" donde no aplique)

### Extracción de Texto (Ingesta)

- [X] T010 [P] [US1] Implement source type detector in `src/extractors/base.py` with function `detect_source(file_path: Path) -> str` returning tipo_fuente: pdf_native, pdf_ocr, docx, image, txt
  - **DoD**: Detección correcta por extensión y mime type, fallback a unknown si no reconocido

- [X] T011 [P] [US1] Implement native PDF extractor in `src/extractors/pdf_native.py` using pdfplumber with function `extract_text_pdf_native(file_path: Path) -> tuple[str, int]` returning (texto, paginas)
  - **DoD**: Prueba con PDF con texto real devuelve longitud > 0 sin errores, preserva saltos de línea básicos

- [X] T012 [P] [US1] Implement scanned PDF OCR extractor in `src/extractors/pdf_ocr.py` using pdf2image + pytesseract with function `extract_text_pdf_ocr(file_path: Path, dpi: int = 300, lang: str = 'spa') -> tuple[str, int]`
  - **DoD**: Prueba con PDF escaneado devuelve texto utilizable (>80% precisión visual), parámetros dpi y lang ajustables

- [X] T013 [P] [US1] Implement DOCX extractor in `src/extractors/docx_extractor.py` using python-docx with function `extract_text_docx(file_path: Path) -> str`
  - **DoD**: Lectura de párrafos y join correcto con saltos de línea, soporta tablas básicas

- [X] T014 [P] [US1] Implement image OCR extractor in `src/extractors/image_extractor.py` using pytesseract with function `extract_text_image(file_path: Path, lang: str = 'spa') -> str`
  - **DoD**: OCR funcional con al menos una imagen de ejemplo (PNG/JPG), detecta texto en español

- [X] T015 [US1] Implement extraction orchestrator in `src/extractors/__init__.py` with function `extract_text_auto(file_path: Path) -> tuple[str, int|None, str]` returning (texto, paginas, tipo_fuente)
  - **DoD**: Intenta PDF nativo primero, si no hay texto o falla aplica fallback OCR automático. Batería de tests con PDF nativo, escaneado, docx, imagen pasan exitosamente

- [X] T016 [US1] Implement text normalization in `src/utils/text_normalizer.py` with function `normalize_text(raw: str) -> str` cleaning espacios múltiples, saltos de línea excesivos, caracteres de control
  - **DoD**: Función retorna texto limpio preservando estructura básica de párrafos, límite de tamaño opcional para truncado

### LLM Local (Ollama) y Prompting

- [X] T017 [P] [US1] Implement Ollama HTTP client in `src/orchestration/ollama_client.py` with function `ollama_generate(model: str, prompt: str, temperature: float = 0.2) -> str` calling POST /api/generate endpoint
  - **DoD**: Función conecta a localhost:11434, retorna texto de respuesta, maneja timeout y errores de conexión con excepciones claras

- [X] T018 [P] [US1] Define internal LLM prompts (CONSTITUTION, SPECIFY, PLAN) in `src/orchestration/prompts.py` as constants in Spanish based on contracts/ollama-prompt.md
  - **DoD**: Constantes LLM_CONSTITUTION, LLM_SPECIFY, LLM_PLAN definidas como strings multi-línea, documentadas con comentarios explicativos

- [X] T019 [US1] Implement prompt assembler in `src/orchestration/prompt_builder.py` with function `build_prompt(texto: str, max_tokens: int = 4000) -> str` composing CONSTITUTION + SPECIFY + PLAN + truncated DOCUMENTO
  - **DoD**: Pruebas unitarias con textos cortos y largos verifican truncado seguro sin cortar palabras, respeta límite de tokens

- [X] T020 [US1] Implement JSON response parser and validator in `src/orchestration/json_validator.py` with function `parse_and_validate(response: str) -> Analisis` extracting JSON block and validating with Pydantic
  - **DoD**: Extrae JSON entre primera { y última }, parsea y valida con schema Analisis, errores controlados con mensaje de corrección

- [X] T021 [US1] Implement retry logic for invalid JSON in `src/orchestration/json_validator.py` with retry_with_correction function attempting up to 2 retries with correction message "Devuelve SOLO JSON válido con el esquema exacto"
  - **DoD**: Reintentos registrados en logs, tras 2 fallos retorna error sin bloquear aplicación

- [X] T022 [US1] Implement confidence heuristic and notes generation in `src/orchestration/postprocessor.py` with function `postprocess_analysis(analisis: Analisis, texto: str) -> Analisis` adjusting confianza_aprox based on category completeness and literal presence of dates/numbers in text
  - **DoD**: Función reduce confianza si categorías vacías >50%, añade notas si valores numéricos no aparecen literales en texto

- [X] T023 [US1] Implement document chunking for long documents in `src/orchestration/chunker.py` with functions `split_text(texto: str, max_chunk_size: int) -> list[str]` and `consolidate_analyses(chunks: list[Analisis]) -> Analisis` merging lists, deduplicating, reconciling conflicts, trimming resumen_bullets to max 10
  - **DoD**: Función split balancea chunks sin cortar oraciones, consolidate merge sin duplicados, prioriza frases densas en información para resumen

### Servicio de Análisis Unificado

- [X] T024 [US1] Implement unified analysis service in `src/orchestration/analyzer.py` with function `analyze_document(file_path: Path) -> tuple[Documento, Analisis, Dupla]` orchestrating pipeline: extracción → normalize → prompt → LLM → validar → postprocesar → crear dupla
  - **DoD**: Maneja errores en cada etapa sin fallos catastróficos, retorna objetos válidos o excepciones con mensajes claros, pipeline completo funciona end-to-end

- [X] T024b [US1] Implement cancellation handler in `src/orchestration/analyzer.py` using `threading.Event` flag checked between pipeline stages, with `st.button("⏹ Cancelar procesamiento")` visible during long operations (>10s)
  - **DoD**: Botón visible solo cuando `st.session_state['processing'] == True`, click detiene pipeline gracefully sin corromper estado, muestra `st.info("Análisis cancelado por usuario")`, permite reintentar con nuevo documento

- [X] T025 [P] [US1] Implement simple language detection heuristic in `src/utils/language_detector.py` with function `detect_language(texto: str) -> str` returning 'es', 'en', 'unknown' based on keyword patterns
  - **DoD**: Rellena idioma_detectado cuando es obvio (>10 palabras en español o inglés), fallback a 'unknown' sin fallos

- [X] T026 [P] [US1] Implement configuration control with flags in `src/utils/config_loader.py` for OCR on/off, OCR language, LLM model name, temperature, export enabled/disabled
  - **DoD**: Lectura de config.yaml o environment variables, override desde UI posible, defaults seguros definidos

- [X] T027 [P] [US1] Implement basic logging and timing measurements in `src/utils/logging_config.py` tracking tiempos por etapa: extracción, OCR, LLM, total
  - **DoD**: Logs visibles en consola con nivel INFO, incluyen timestamps y duración de operaciones, archivo opcional logs/app.log

### UI Streamlit (Visualización)

- [X] T028 [US1] Create Streamlit base page in `src/ui/app.py` with `st.set_page_config(page_title="Analizador de Documentos Legales", layout="wide")` and main entry point
  - **DoD**: App corre exitosamente con `streamlit run src/ui/app.py`, muestra título y layout wide

- [X] T029 [US1] Implement file uploader in `src/ui/components/file_uploader.py` with `st.file_uploader(accept_multiple_files=True, type=['pdf', 'docx', 'png', 'jpg'])` and safe temporary file handling
  - **DoD**: Acepta PDF/DOCX/Imágenes, lista de archivos leídos mostrada, guardado temporal seguro con limpieza automática

- [X] T029b [US1] Implement file size validator in `src/ui/components/file_uploader.py` checking `uploaded_file.size` before processing, rejecting files >100MB with `st.error("Archivo demasiado grande. Máximo: 100MB. Sugerencia: divide el documento o comprime el PDF.")`
  - **DoD**: Validación ocurre ANTES de guardado temporal, archivos rechazados no consumen recursos, en batch solo afecta archivo específico (otros continúan), mensaje muestra tamaño actual y límite

- [X] T030 [US1] Implement session state management in `src/ui/app.py` initializing `st.session_state['duplas']` (list) and `st.session_state['selected_id']` (str|None)
  - **DoD**: Persistencia en memoria de sesión funciona entre reruns, duplas mantienen estado correcto

- [X] T031 [US1] Create analysis view with cards/bullets in `src/ui/components/analysis_view.py` displaying 8 categorías con secciones: Partes, Fechas, Importes, Obligaciones, Derechos, Riesgos, Resumen, Tipo Documento. Use `st.expander` for each category and `st.markdown` for bullet lists
  - **DoD**: Visual coherente y escaneable, métricas básicas mostradas (páginas, tipo_fuente, caracteres, timestamp), categorías vacías muestran "No disponible"

- [X] T032 [US1] Implement progress indicators in `src/ui/app.py` with spinners for "Extrayendo texto...", "OCR en progreso...", "Analizando con IA local..." using `st.spinner()` and `st.progress()`
  - **DoD**: UX fluida en pruebas, mensajes de error amigables (st.error) sin bloquear aplicación

**Checkpoint**: User Story 1 (MVP) complete - user can analyze single document and view results

---

## Phase 4: User Story 2 - Historial de Duplas (Priority: P2)

**Goal**: Mantener historial persistente de todas las duplas (documento ↔ análisis) en lista lateral, seleccionables para recuperar análisis, con opción de eliminar entradas

**Independent Test**: Después de analizar 3 documentos, verificar que los 3 aparecen en historial lateral, cada uno seleccionable y eliminable

### Persistencia (JSON Storage)

- [X] T033 [US2] Implement history save/load in `src/persistence/json_store.py` with functions `save_history(duplas: list[Dupla], path: Path)` and `load_history(path: Path) -> list[Dupla]` using duplas.json file
  - **DoD**: Autosave tras análisis correcto, carga al iniciar app, manejo de archivo corrupto sin crash

- [X] T034 [US2] Implement replacement policy in `src/persistence/json_store.py` handling duplicate document IDs (same hash): option to overwrite or create new version with timestamp suffix
  - **DoD**: Comportamiento definido y documentado en código con comentarios, tests verifican ambas opciones

- [ ] T035 [P] [US2] (Optional - SKIPPED) Create SQLite persistence layer in `src/persistence/sqlite_store.py` with tables documentos, analisis, duplas, versiones
  - **DoD**: CRUD básico funcional, migración desde JSON con script `migrate_json_to_sqlite.py`, queries por fecha/tipo optimizadas con índices

### UI - Historia Sidebar

- [X] T036 [US2] Create history sidebar in `src/ui/components/history_sidebar.py` displaying duplas as clickable list with nombre archivo, tipo documento, fecha análisis, estado badge. Include delete button with confirmation dialog using `st.sidebar` and `st.button`
  - **DoD**: Navegación correcta entre duplas (click selecciona), botón eliminar solicita confirmación (st.warning "¿Eliminar este análisis?"), tras aceptar desaparece sin afectar otras

- [X] T036b [US2] Implement history sorting controls in `src/ui/components/history_sidebar.py` with `st.radio` selector for ordering: "Más reciente" (default), "Más antiguo", "Alfabético A-Z"
  - **DoD**: Selector visible en sidebar superior, cambio de orden re-renderiza lista inmediatamente, ordenamiento persistido en `st.session_state['sort_order']`, cronológico descendente por defecto al iniciar app

**Checkpoint**: User Story 2 complete - persistent history fully functional

---

## Phase 5: User Story 3 - Carga y Análisis Múltiple (Priority: P2)

**Goal**: Cargar varios documentos simultáneamente, procesar cada uno individualmente, mantener estructura visual consistente para comparación

**Independent Test**: Cargar 3 documentos de diferentes formatos (PDF, DOCX, imagen), verificar que todos se analizan y aparecen en historial con estructura consistente

- [X] T037 [US3] Extend file uploader and analyzer in `src/ui/app.py` to handle multiple files with batch processing loop, global progress indicator "Procesando 3 de 5...", error handling per file without stopping batch
  - **DoD**: Acepta múltiples archivos, muestra progreso global con st.progress, documentos que fallan muestran error pero continúa procesando restantes, todas las duplas aparecen en historial tras completar

**Checkpoint**: User Story 3 complete - batch document processing works

---

## Phase 6: User Story 4 - Exportación de Resultados (Priority: P3)

**Goal**: Exportar análisis de un documento en formato JSON estructurado preservando todas las categorías, permitiendo uso externo sin alterar visualización

**Independent Test**: Exportar un análisis completo, abrir archivo generado, confirmar que contiene todas las categorías con formato estructurado legible

- [X] T038 [US4] Implement export functionality in `src/ui/components/export_buttons.py` with button "Exportar JSON" using `st.download_button` generating JSON file with structure {documento: {...}, analisis: {...}, metadata: {...}} preserving UTF-8 encoding
  - **DoD**: Archivo generado con nombre `{nombre_documento}-{timestamp}.json`, categorías vacías como arrays vacíos, caracteres especiales (ñ, €) preservados correctamente

- [X] T039 [US4] Implement import history functionality in `src/ui/app.py` with button "Importar Historial" using `st.file_uploader(type='json')` loading duplas.json and merging with current state
  - **DoD**: Merge simple o reemplazo (decisión definida en código), sin duplicados, validación de schema antes de importar

**Checkpoint**: User Story 4 complete - export/import fully functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Testing, documentation, robustness, and optional improvements

### Testing y Validación (Quality Assurance)

- [X] T040 [P] Create unit tests for text extraction in `tests/unit/test_extractors.py` testing PDF native, PDF OCR, DOCX, image extractors with fixtures from `tests/fixtures/`
  - **DoD**: Suite mínima con al menos 1 fixture por tipo, tests verifican longitud >0 y ausencia de errores, cobertura >80% de extractors/

- [X] T041 [P] Create unit tests for JSON parser/validator in `tests/unit/test_json_validator.py` testing casos: JSON correcto, JSON con ruido (texto antes/después), JSON inválido, campos faltantes
  - **DoD**: Parser robusto maneja todos los casos, errores claros especifican qué campo falta o qué formato es inválido

- [X] T042 [P] Create integration test for chunking and consolidation in `tests/integration/test_chunker.py` using synthetic long document (50 páginas) verifying consolidated análisis coherente
  - **DoD**: Bullets recortados a 10 máximo, listas deduplicadas correctamente, fechas/importes reconciliados sin conflictos

- [X] T043 [P] Measure local performance in `tests/performance/` for typical documents (5-10 págs PDF nativo, 5 págs escaneado) recording tiempos de extracción, OCR, LLM, total
  - **DoD**: Métricas anotadas en README.md sección Performance, documentado hardware de prueba (CPU, RAM, GPU si aplica)

- [X] T044 [P] Validate privacy compliance by reviewing code for external calls: ensure no requests to services other than localhost:11434 (Ollama)
  - **DoD**: Checklist de cumplimiento de constitución en docs/privacy-compliance.md verificando Principio I, sin telemetría, sin analytics

### Documentación y Entregables

- [X] T045 [P] Create comprehensive README.md at repository root with sections: Overview, Features, Installation (Python, Tesseract, Ollama), Quick Start, Usage, Troubleshooting, Privacy Guarantees
  - **DoD**: Usuario nuevo puede arrancar en <10 minutos siguiendo guía, enlaces a instaladores externos funcionan, screenshots opcionales de UI

- [X] T046 [P] Create internal prompts guide in `docs/prompts.md` documenting cómo cambiar LLM_CONSTITUTION, SPECIFY, PLAN con ejemplos, ajustar temperatura, cambiar modelo Ollama
  - **DoD**: Ejemplos y consejos claros, referencia a contracts/ollama-prompt.md como fuente completa

- [X] T047 [P] Create troubleshooting guide in `docs/troubleshooting.md` covering common issues: OCR pobre (aumentar DPI), JSON inválido (revisar prompts), documento enorme (chunking), Ollama offline (health check)
  - **DoD**: Soluciones y parámetros recomendados por problema, comandos de verificación incluidos

- [X] T048 [P] Create roadmap document in `docs/roadmap.md` listing future features: SQLite migration, advanced document classification, history filtering/search, multi-language UI, comparative analysis (diff 2 documents)
  - **DoD**: Sección en README.md o ROADMAP.md con timeline estimado (opcional), prioridades marcadas

### UI - Configuración Avanzada

- [X] T049 [P] Add configuration options UI in `src/ui/pages/settings.py` (or settings expander) with selects for: LLM model (llama3.2:3b, phi3:mini, mistral:7b), temperature slider (0.1-0.5), OCR language (spa, spa+eng, eng), chunking enabled/disabled
  - **DoD**: Cambios afectan análisis subsecuente, valores persistidos en st.session_state, reset a defaults disponible

### Mejoras Opcionales (Post-MVP)

- [X] T050 [P] Implement post-processing enhancements in `src/utils/postprocessor.py` with regex for EU/ES date normalization (DD/MM/YYYY → YYYY-MM-DD), currency symbol standardization (€ → EUR, $ → USD)
  - **DoD**: Mejoras visibles en importes/fechas normalizadas, backwards compatible con análisis previos

- [X] T051 [P] Implement snippet/citation mapping in `src/orchestration/citation_mapper.py` mapping frases de obligaciones/derechos a oraciones del texto original con line numbers
  - **DoD**: Posibilidad de mostrar snippet de apoyo en UI (st.info con texto original), mejora verificabilidad de extracción

- [X] T052 [P] Enhance document type detection in `src/utils/document_classifier.py` with keyword-based heuristics for "contrato laboral", "nómina", "convenio", "poder notarial"
  - **DoD**: Mayor estabilidad del campo tipo_documento (>90% precisión en documentos estándar), fallback a LLM si heurísticas fallan

**Checkpoint**: All enhancements complete - production-ready application

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **Phase 3 (US1 - MVP)**: Depends on Phase 2 - Must complete before US2/US3/US4
- **Phase 4 (US2)**: Depends on Phase 2 and Phase 3 (T028-T032 for UI integration)
- **Phase 5 (US3)**: Depends on Phase 2 and Phase 3 (T024 analyzer, T029 uploader)
- **Phase 6 (US4)**: Depends on Phase 2 and Phase 3 (T006-T009 models, T030 session state)
- **Phase 7 (Polish)**: Depends on completion of US1 (MVP) at minimum, ideally all user stories

### User Story Dependencies

**Critical Path (MVP)**:
```
Setup (T001-T005) → Foundational (T006-T009) → US1 Complete (T010-T032)
```

**Parallel Opportunities After Foundational**:
- US1 tasks within categories can run in parallel:
  - Extractors (T010-T014) - all [P]
  - Prompts (T017-T018) - both [P]
  - Logging, config, language detection (T025-T027) - all [P]
- US2, US3, US4 can start after US1 T028-T032 (UI foundation) complete

### Within Each Phase

**Phase 3 (US1) Internal Order**:
1. Extractors (T010-T016) - can work in parallel, T015 depends on T010-T014
2. LLM (T017-T023) - T017-T018 parallel, T019 depends on T018, T020-T023 sequential
3. Service (T024-T027) - T024 depends on T015+T019+T020, T025-T027 parallel
4. UI (T028-T032) - T028 first, T029-T032 parallel after T028

**Parallel Execution Example (US1 Extractors)**:
```bash
# After Foundational complete, start all extractors in parallel
Task T010 (detector) &      # Developer 1
Task T011 (PDF native) &    # Developer 2
Task T012 (PDF OCR) &       # Developer 3
Task T013 (DOCX) &          # Developer 4
Task T014 (Image) &         # Developer 5
wait                         # All complete
Task T015 (orchestrator)    # Depends on T010-T014
```

### Suggested Execution Sequence (Single Developer)

**Week 1 - MVP Foundation**:
- Day 1-2: Setup (T001-T005) + Foundational (T006-T009)
- Day 3-4: US1 Extractors (T010-T016) + LLM setup (T017-T018)
- Day 5: US1 LLM pipeline (T019-T023)

**Week 2 - MVP Completion**:
- Day 6: US1 Service (T024-T027)
- Day 7: US1 UI (T028-T032)
- Day 8: US2 Persistence + History (T033-T036)
- Day 9: US3 Batch processing (T037)
- Day 10: US4 Export (T038-T039)

**Week 3 - Polish & Delivery**:
- Day 11-12: Testing (T040-T044)
- Day 13-14: Documentation (T045-T048)
- Day 15: Optional improvements (T049-T052) or deployment

---

## Implementation Strategy

### MVP-First Approach

**Minimum Viable Product (MVP) = Phase 1 + Phase 2 + Phase 3 (US1)**

This delivers:
- ✅ Single document analysis (core value proposition)
- ✅ 8 structured categories extraction
- ✅ Visual presentation in Streamlit UI
- ✅ Local processing with privacy guarantees
- ✅ Support for PDF (native/scanned), DOCX, images

**MVP validates**: Technical feasibility, user value, constitutional compliance

### Incremental Delivery After MVP

**Increment 1 (US2)**: Add persistent history → enables recurring users workflow

**Increment 2 (US3)**: Add batch processing → enables professional/high-volume use cases

**Increment 3 (US4)**: Add export → enables integration with external tools

**Increment 4 (Polish)**: Testing, documentation, performance optimization

### Risk Mitigation Tasks

**High-Risk Tasks** (address early):
- T012 (PDF OCR): OCR quality varies significantly - test with diverse fixtures early
- T020-T021 (JSON parsing/retry): LLM output can be unpredictable - robust validation critical
- T023 (Chunking): Complex consolidation logic - thorough testing required
- T024 (Analyzer pipeline): Integrates all components - end-to-end test essential

**Success Criteria Verification**:
- After T024: Measure analysis time (SC-005: <30s for 10-20 pages)
- After T020: Measure JSON validation success rate (>85% first attempt)
- After T031: Validate visual consistency (SC-011: same category order 100%)
- After T044: Verify privacy (SC-008: 0% data transmission)

---

## Task Count Summary

- **Total Tasks**: 55
- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 4 tasks (CRITICAL - blocks all user stories)
- **Phase 3 (US1 - MVP)**: 25 tasks (45% of total effort)
- **Phase 4 (US2)**: 5 tasks
- **Phase 5 (US3)**: 1 task (extends existing)
- **Phase 6 (US4)**: 2 tasks
- **Phase 7 (Polish)**: 13 tasks

**Parallelizable Tasks**: 24 marked with [P] (44% of total)

**MVP Delivery**: T001-T032 + T024b + T029b (34 tasks = 62% of total)

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] All US1 acceptance scenarios from spec.md pass
- [ ] All US2 acceptance scenarios from spec.md pass
- [ ] All US3 acceptance scenarios from spec.md pass
- [ ] All US4 acceptance scenarios from spec.md pass
- [ ] All 9 constitutional principles validated (see plan.md Constitution Check)
- [ ] Success criteria SC-001 through SC-012 measured and documented
- [ ] quickstart.md validated end-to-end by external user
- [ ] Privacy compliance: no external calls except localhost:11434
- [ ] Performance goals met: <30s for 10-20 page PDF native
- [ ] Error handling: 0 catastrophic failures in test suite

---

**Ready to implement**: Run `/speckit.implement` to begin execution
