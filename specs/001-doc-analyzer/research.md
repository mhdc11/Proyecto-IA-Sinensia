# Research & Technology Decisions

**Feature**: Analizador de Documentos Legales
**Date**: 2026-02-18
**Phase**: 0 (Research & Decision Making)

## Overview

Este documento registra las decisiones tecnológicas tomadas para implementar el analizador de documentos legales con procesamiento 100% local, respetando los principios constitucionales de privacidad, veracidad y simplicidad.

---

## Decision 1: Language & Runtime

### Question
¿Qué lenguaje y runtime usar para una aplicación de ML/NLP con UI local?

### Decision
**Python 3.10+** como lenguaje principal

### Rationale

**Fortalezas**:
- Ecosistema maduro para ML/NLP:
  - Binding nativos de Ollama (biblioteca oficial)
  - Bibliotecas de procesamiento de documentos (pdfplumber, python-docx, pytesseract)
  - Pydantic para validación de schemas
- Streamlit disponible (framework UI rápido para apps de ML)
- Compatibilidad multiplataforma (Windows, macOS, Linux) sin cambios de código
- Curva de aprendizaje suave para mantenimiento futuro
- Deployment local simple (`python app.py` o `streamlit run`)

**Debilidades**:
- Performance inferior a lenguajes compilados (Rust, Go) para procesamiento intensivo
  - **Mitigación**: Operaciones lentas (OCR, LLM inference) delegadas a binarios nativos (Tesseract, Ollama)
- Global Interpreter Lock (GIL) limita paralelismo de threads
  - **Mitigación**: Procesamiento de documentos múltiples en serie (suficiente para single-user local)

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **Rust + Tauri** | Performance excepcional, binarios nativos pequeños | Curva de aprendizaje alta, ecosistema LLM inmaduro | Over-engineering para MVP, desarrollo 3x más lento |
| **Node.js + Electron** | Ecosistema web maduro, UI con React/Vue | Binaries pesados (>100MB), bindings OCR/PDF limitados | Overhead innecesario, peor integración con ML stack |
| **Java + JavaFX** | Portabilidad JVM, robustez empresarial | Startup lento, ecosistema ML menos rico que Python | Experiencia de usuario degradada (startup tiempo) |

### Best Practices
- Usar `pyenv` o `conda` para gestión de versiones de Python
- Virtual environments obligatorios (venv/poetry) para aislar dependencias
- Type hints en todo el código (mypy para static checking)
- Pin versions estricto en `requirements.txt` (evitar breaking changes)

### References
- [Python for Document Processing](https://realpython.com/pdf-python/)
- [Ollama Python Library](https://github.com/ollama/ollama-python)

---

## Decision 2: UI Framework

### Question
¿Qué framework usar para la interfaz de usuario local sin complejidad de frontend tradicional?

### Decision
**Streamlit 1.30+**

### Rationale

**Fortalezas**:
- **Zero frontend code**: UI completa en Python puro (no HTML/CSS/JS)
- **Components ricos**: file uploader, sidebar, expanders, dataframes, charts out-of-the-box
- **Reactive model**: Re-run script en cada interacción (simplicidad mental)
- **Local-first**: `streamlit run app.py` abre localhost:8501, no requiere servidor externo
- **Comunidad activa**: 40k+ estrellas GitHub, documentación extensa, plugins disponibles

**Debilidades**:
- Reruns completos pueden ser lentos con estado complejo
  - **Mitigación**: `st.session_state` para cachear datos pesados (historial, análisis previos)
- Customización limitada de estilos
  - **Mitigación**: Suficiente para MVP, futura migración a FastAPI+React si se requiere branding

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **Flask + Jinja2 templates** | Control total sobre UI, más ligero | Requiere escribir HTML/CSS, no reactive | 5x más código frontend, desarrollo más lento |
| **FastAPI + React** | Separación backend/frontend, UI moderna | Overhead de 2 proyectos, build pipeline complejo | Over-engineering para single-user local |
| **Jupyter Notebooks** | Exploratorio, ideal para prototipado | No apto para end-users no técnicos | UI no production-ready |
| **PyQt/Tkinter** | UI nativa, no requiere navegador | Código verbose, curva de aprendizaje UI widgets | Desarrollo 3-4x más lento que Streamlit |

### Best Practices
- Usar `st.cache_data` para operaciones costosas (lectura de duplas.json)
- `st.session_state` para persistir estado entre reruns (selección actual, filtros)
- Config en `.streamlit/config.toml` (tema, puertos, recursos)
- Evitar lógica compleja en UI (mover a capas de servicio)

### References
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Best Practices](https://blog.streamlit.io/common-app-problems-resource-limits/)

---

## Decision 3: PDF Text Extraction

### Question
¿Qué biblioteca usar para extraer texto de PDFs nativos (con texto embebido)?

### Decision
**pdfplumber 0.10+**

### Rationale

**Fortalezas**:
- Balance extracción/layout: preserva estructura de tablas, columnas
- Detección automática de regiones de texto vs imágenes
- API simple: `pdf.pages[0].extract_text()`
- Manejo robusto de PDFs complejos (columnas múltiples, headers/footers)
- Open-source (MIT license) sin restricciones

**Debilidades**:
- Performance moderado en PDFs muy grandes (50+ páginas)
  - **Mitigación**: Suficiente para 98% de casos (1-50 páginas), chunking para documentos extremos
- No soporta PDFs cifrados con contraseña
  - **Mitigación**: Mensaje de error claro al usuario ("Desbloquea el PDF antes de cargar")

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **PyPDF2** | Ligero, ampliamente usado | Extracción básica, pierde layout de tablas | Calidad insuficiente para contratos complejos |
| **pymupdf (PyMuPDF)** | Muy rápido, soporta muchos formatos | Licencia AGPL (restrictiva para comercial) | Riesgo legal futuro si se comercializa |
| **pdfminer.six** | Extracción de bajo nivel, flexible | API compleja, curva de aprendizaje alta | Over-engineering, desarrollo más lento |
| **Camelot** | Especializado en tablas | Requiere dependencias pesadas (Ghostscript) | Overhead para casos de uso general |

### Best Practices
- Detectar PDFs vacíos o solo imágenes antes de extraer (evitar falsos positivos)
- Normalizar texto extraído (quitar espacios múltiples, saltos de línea redundantes)
- Timeout de 30 segundos por PDF (evitar bloqueos con PDFs corruptos)

### Code Example
```python
import pdfplumber

def extract_pdf_native(path: Path) -> tuple[str, int]:
    with pdfplumber.open(path) as pdf:
        text = "\n\n".join(page.extract_text() for page in pdf.pages)
        return (text.strip(), len(pdf.pages))
```

### References
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber)
- [PDF Extraction Comparison](https://github.com/py-pdf/benchmarks)

---

## Decision 4: DOCX Text Extraction

### Question
¿Qué biblioteca usar para extraer texto de documentos DOCX?

### Decision
**python-docx 1.1+**

### Rationale

**Fortalezas**:
- Estándar de facto para DOCX en Python
- Soporta estilos (bold, italic), listas, tablas
- API intuitiva: `doc.paragraphs` para iterar texto
- Activamente mantenido (última release 2023)
- Open-source (MIT license)

**Debilidades**:
- No soporta formatos antiguos (.doc) → solo .docx (Office 2007+)
  - **Mitigación**: Mensaje claro "Convierte .doc a .docx" (formatos legacy raros en documentos recientes)

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **docx2txt** | Muy ligero, solo texto plano | Pierde estructura (tablas, estilos) | Insuficiente para documentos complejos |
| **mammoth** | Convierte DOCX → HTML | Overhead innecesario (no necesitamos HTML) | Over-engineering para extracción pura |
| **Aspose.Words** | Soporte comercial, features extensas | Licencia de pago, overkill para extracción básica | Costo no justificado para MVP |

### Best Practices
- Extraer texto de párrafos y tablas por separado, luego concatenar
- Preservar estructura de listas (identificar bullets/numeración)
- Normalizar saltos de línea dentro de celdas de tabla

### Code Example
```python
from docx import Document

def extract_docx(path: Path) -> str:
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    tables = [[cell.text for cell in row.cells] for table in doc.tables for row in table.rows]
    return "\n\n".join(paragraphs + ["\n".join(" | ".join(row) for row in tables)])
```

### References
- [python-docx Documentation](https://python-docx.readthedocs.io/)

---

## Decision 5: OCR Engine

### Question
¿Qué motor OCR usar para documentos escaneados e imágenes?

### Decision
**Tesseract 5.x + pytesseract 0.3.10+ + pdf2image 1.16+**

### Rationale

**Fortalezas (Tesseract)**:
- Open-source maduro (Google, 15+ años desarrollo)
- Soporta 100+ idiomas incluido español con entrenamiento específico
- Detección automática de layout (columnas, bloques de texto)
- Mejoras recientes en accuracy (Tesseract 5 usa LSTM neural nets)

**Fortalezas (pytesseract)**:
- Wrapper Python oficial de Tesseract
- API simple: `pytesseract.image_to_string(image, lang='spa')`

**Fortalezas (pdf2image)**:
- Convierte PDF pages a imágenes PIL para OCR
- Usa poppler (rápido, robusto)

**Debilidades**:
- Requiere instalación del binario Tesseract en sistema (no puro Python)
  - **Mitigación**: Documentado en quickstart.md, instaladores disponibles para Windows/macOS/Linux
- Performance: ~2-5 segundos por página a 300 DPI
  - **Mitigación**: Aceptable para documentos típicos (5-10 páginas = 10-50 seg total)
- Accuracy variable con documentos de baja calidad
  - **Mitigación**: Advertencias en UI, opción de aumentar DPI a 400

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **Google Vision API** | Accuracy superior, detección de tablas | Cloud, pago por uso, viola Principio I | Privacidad comprometida |
| **AWS Textract** | Extracción de forms, tablas complejas | Cloud, pago, latencia de red | Privacidad + costo |
| **EasyOCR** | Python puro, no requiere Tesseract binario | Modelos grandes (100MB+), inference lento | Overhead de descarga inicial |
| **PaddleOCR** | Alta accuracy, modelos livianos | Menor soporte de idiomas, documentación en chino | Menor madurez de ecosistema |

### Best Practices
- **DPI óptimo**: 300 DPI (balance speed/quality), 400 DPI para documentos críticos
- **Preprocessing**: Binarización (umbral Otsu), deskew (detección de ángulo), denoising
- **Idiomas**: `lang='spa'` para español, `lang='spa+eng'` para documentos híbridos
- **Chunking**: 1 página a la vez para gestión de memoria (PDFs grandes)
- **Validación**: Verificar texto extraído no vacío, advertir si <50 caracteres por página

### Code Example
```python
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageFilter

def extract_pdf_ocr(path: Path, dpi: int = 300) -> tuple[str, int]:
    images = convert_from_path(path, dpi=dpi)
    texts = []
    for img in images:
        # Preprocessing: binarize + denoise
        img_gray = img.convert('L')
        img_binary = img_gray.point(lambda x: 0 if x < 128 else 255, '1')
        text = pytesseract.image_to_string(img_binary, lang='spa+eng')
        texts.append(text)
    return ("\n\n---PAGE BREAK---\n\n".join(texts), len(images))
```

### References
- [Tesseract Documentation](https://tesseract-ocr.github.io/)
- [pytesseract GitHub](https://github.com/madmaze/pytesseract)
- [OCR Preprocessing Best Practices](https://pyimagesearch.com/2021/11/22/improving-ocr-results-with-basic-image-processing/)

---

## Decision 6: Local LLM for Analysis

### Question
¿Qué solución de LLM local usar para análisis de texto estructurado sin cloud/pago?

### Decision
**Ollama + llama3.2:3b**

### Rationale

**Fortalezas (Ollama)**:
- Servicio local HTTP (REST API simple, no requiere Hugging Face/PyTorch complejos)
- Gestión automática de modelos (download, cache, updates)
- GPU acceleration opcional (CUDA, Metal, ROCm)
- Cross-platform (Windows, macOS, Linux)
- Open-source, sin costos de uso

**Fortalezas (llama3.2:3b)**:
- **Balance óptimo**: 2GB VRAM, inference 2-5 seg en CPU moderno, 4K context window
- **Seguimiento de instrucciones**: Bueno para tareas de extracción estructurada (JSON output)
- **Multilenguaje**: Entrenado en español e inglés
- **Meta open-source**: Sin restricciones de uso comercial

**Debilidades**:
- Puede alucinar entidades similares pero no exactas (ej: "ACME Corp" → "ACME Corporation")
  - **Mitigación**: Validación heurística post-análisis, campo `confianza_aprox` refleja incertidumbre
- Context window 4K tokens limita documentos a ~10 páginas single-pass
  - **Mitigación**: Chunking con consolidación inteligente para docs >10 páginas
- Inconsistencia ocasional en formato JSON
  - **Mitigación**: Reintentos con prompt de corrección, validación Pydantic estricta

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **GPT-4 API (OpenAI)** | Accuracy superior, context 128K | Cloud, pago ($), viola Principio I | Privacidad + costo recurrente |
| **Claude API (Anthropic)** | Excelente para análisis largo | Cloud, pago, viola Principio I | Privacidad comprometida |
| **phi3:mini (Ollama)** | Ligero (1GB), rápido | Menor calidad de extracción de entidades complejas | Degradación de quality no justificada |
| **mistral:7b (Ollama)** | Mayor accuracy | Requiere 8GB+ RAM, inference lento (5-10 seg) | Overhead de recursos para ganancia marginal |
| **llama.cpp directo** | Control total, sin servicio intermedio | Requiere compilación, gestión manual de modelos | Complejidad operacional innecesaria |

### Model Comparison Table

| Model | Size | VRAM | Inference Time (CPU) | Context Window | Quality | Use Case |
|-------|------|------|---------------------|----------------|---------|----------|
| **llama3.2:3b** ✅ | 2GB | 2GB | 2-5 seg | 4K | ⭐⭐⭐⭐ | **Balanced (SELECTED)** |
| phi3:mini | 1GB | 1GB | 1-3 seg | 4K | ⭐⭐⭐ | Hardware limitado |
| mistral:7b | 5GB | 5GB | 5-10 seg | 8K | ⭐⭐⭐⭐⭐ | Hardware potente |

### Best Practices
- **Temperature baja (0.1-0.3)**: Reduce creatividad, aumenta determinismo
- **System prompt robusto**: Incluir Constitution, examples few-shot, esquema JSON explícito
- **Format enforcement**: Usar parámetro `format: "json"` en Ollama API (fuerza output JSON válido)
- **Timeouts generosos**: 60 segundos para inference en CPU
- **Reintentos con backoff**: 3 intentos con delay 2^n segundos si Ollama no responde
- **Streaming off**: `stream: false` para análisis completo en una respuesta (simplifica parsing)

### Code Example
```python
import requests

def analyze_with_ollama(text: str, model: str = "llama3.2:3b") -> dict:
    prompt = f"""CONSTITUTION: No inventes datos. Solo extrae info presente.
ESQUEMA: {json_schema}
DOCUMENTO: {text[:4000]}  # Truncar a context window
"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "temperature": 0.2,
            "stream": false,
            "format": "json"
        },
        timeout=60
    )
    return response.json()["response"]
```

### References
- [Ollama Documentation](https://ollama.com/docs)
- [llama3.2 Model Card](https://ollama.com/library/llama3.2)
- [Llama 3 Technical Report](https://ai.meta.com/blog/meta-llama-3/)

---

## Decision 7: Data Validation & Schemas

### Question
¿Qué framework usar para validación de schemas y serialización JSON?

### Decision
**Pydantic 2.5+**

### Rationale

**Fortalezas**:
- **Type-safe**: Validación en runtime usando Python type hints
- **Auto-serialización**: `.model_dump()` → dict/JSON, `.model_validate()` ← dict
- **Error messages claros**: Describe exactamente qué campo falló y por qué
- **Performance**: Pydantic v2 usa Rust internamente (10-50x más rápido que v1)
- **JSON Schema generation**: Export automático para documentación (contracts/)

**Debilidades**:
- Overhead mínimo de validación en hot paths
  - **Mitigación**: Irrelevante comparado con latencia de LLM (segundos) y OCR

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **marshmallow** | Maduro, flexible | Menos type-safe, no usa type hints nativos | Menos pythonic, más verbose |
| **dataclasses + manual validation** | Stdlib, zero dependencies | Boilerplate code, error handling manual | Reinventa la rueda |
| **attrs + cattrs** | Ligero, flexible | Menos integración con ecosystem | Menor adopción que Pydantic |

### Best Practices
- Usar `Field(..., description="...")` para documentar cada campo
- Validators custom para lógica compleja (`@field_validator`)
- `ConfigDict(strict=True)` para rechazar tipos incorrectos
- `ConfigDict(extra='forbid')` para detectar campos extra del LLM

### Code Example
```python
from pydantic import BaseModel, Field, field_validator

class Fecha(BaseModel):
    etiqueta: str = Field(..., description="Tipo de fecha (inicio, fin, vencimiento)")
    valor: str = Field(..., description="Fecha en ISO (YYYY-MM-DD) o literal")

    @field_validator('valor')
    def validate_fecha_format(cls, v):
        if not (is_iso_date(v) or is_natural_date(v)):
            raise ValueError("Fecha debe ser ISO o literal válido")
        return v

class Analisis(BaseModel):
    tipo_documento: str
    partes: list[str]
    fechas: list[Fecha]
    # ... resto de campos
```

### References
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic Performance](https://docs.pydantic.dev/latest/concepts/performance/)

---

## Decision 8: Persistence Layer

### Question
¿Qué solución de almacenamiento usar para historial de análisis (duplas)?

### Decision
**JSON file (MVP) → SQLite (Fase 2)**

### Rationale

**MVP (JSON file - duplas.json)**:

**Fortalezas**:
- Zero setup (no database installation)
- Human-readable (fácil debug, backup con git)
- Serialización directa desde Pydantic (`.model_dump_json()`)
- Compatible con Constitution (local, no cloud)

**Debilidades**:
- Performance degrada con >1000 duplas (load completo en memoria)
- No soporta queries complejas (filtrar por fecha, tipo_documento)
- Riesgo de corrupción con escrituras concurrentes
  - **Mitigación**: App single-user local (no concurrencia real)

**Fase 2 (SQLite)**:

**Fortalezas**:
- Queries rápidas con índices (WHERE tipo_documento = 'contrato_laboral')
- Transacciones ACID (no corrupción)
- Soporte de versiones (múltiples análisis del mismo documento)
- Schema migrations con Alembic

**Debilidades**:
- Requiere definir schema SQL
- Más complejo de debug que JSON plano

**Mitigación de transición**:
- Script de migración `json_to_sqlite.py` para importar duplas.json existente
- Mantener backward compatibility: permitir leer duplas.json legacy

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **PostgreSQL** | Potente, features avanzadas | Requiere servidor, overhead para single-user | Over-engineering para local app |
| **MongoDB** | Schema flexible, JSON nativo | Requiere servidor, overhead de recursos | Innecesario para datos estructurados simples |
| **TinyDB** | Python puro, API simple | Performance peor que SQLite | SQLite superior y ya instalado en Python |

### Best Practices (JSON)
- **Atomic writes**: Write to temp file → rename (evita corrupción mid-write)
- **Validation antes de guardar**: Validar Pydantic models antes de serializar
- **Backup automático**: Copiar `duplas.json` a `duplas.json.bak` antes de write

### Best Practices (SQLite - Fase 2)
- **ORM ligero**: SQLModel (= Pydantic + SQLAlchemy) para mantener consistency con schemas
- **Indices**: CREATE INDEX en `tipo_documento`, `ts_creacion` para queries comunes
- **WAL mode**: Write-Ahead Logging para mejor concurrencia (aunque no crítico para single-user)

### Migration Path
```python
# Fase 1 (JSON)
def save_dupla(dupla: Dupla):
    duplas = load_duplas()  # Cargar JSON existente
    duplas[dupla.id] = dupla.model_dump()
    with atomic_write('duplas.json') as f:
        json.dump(duplas, f, indent=2, ensure_ascii=False)

# Fase 2 (SQLite)
from sqlmodel import Session, create_engine
engine = create_engine("sqlite:///duplas.db")

def save_dupla(dupla: Dupla):
    with Session(engine) as session:
        session.add(dupla)  # SQLModel handles serialization
        session.commit()
```

### References
- [SQLite When to Use](https://sqlite.org/whentouse.html)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---

## Decision 9: Chunking Strategy for Long Documents

### Question
¿Cómo manejar documentos que exceden el context window del LLM (4K tokens)?

### Decision
**Sliding window con overlap + consolidación inteligente**

### Rationale

**Problema**:
- llama3.2:3b tiene context window de ~4K tokens (~3000 palabras, ~10 páginas de texto denso)
- Documentos legales de 20-50 páginas exceden límite

**Solución**:

1. **Chunking**:
   - Dividir texto en chunks de ~2500 palabras (deja margen para prompt de sistema)
   - Overlap de 200 palabras entre chunks (preserva contexto en fronteras)
   - Respetar fronteras de párrafos (no cortar frases)

2. **Análisis por chunk**:
   - Cada chunk genera JSON parcial con mismo schema
   - Prompts idénticos para consistency

3. **Consolidación**:
   - **Partes**: Unión de listas, deduplicación por similitud >90% (Levenshtein)
   - **Fechas**: Unión, deduplicación por valor exacto
   - **Importes**: Unión, deduplicación por valor + concepto similar
   - **Obligaciones/Derechos/Riesgos**: Unión, deduplicación fuzzy
   - **Resumen**: Merge de todos los bullets, recortar a 10 más informativos (TF-IDF scoring)
   - **Conflictos**: Si chunks reportan valores contradictorios (ej: fecha inicio diferente), conservar todos + nota en `analisis.notas`

4. **Metadata de confianza**:
   - `confianza_aprox` = promedio de confianzas de chunks individuales
   - Si hay conflictos, bajar confianza en 20%

### Alternatives Considered

| Alternativa | Pros | Cons | Razón de Descarte |
|-------------|------|------|-------------------|
| **Map-Reduce (summarize → re-analyze)** | Más coherente en teoría | 2 pasadas de LLM (2x latencia), pierde detalles | Degradación de calidad |
| **Embeddings + RAG** | Permite queries específicos | Requiere vector DB, over-engineering | Complejidad innecesaria para MVP |
| **Usar modelo más grande (mistral:7b 8K context)** | No requiere chunking | 2x recursos, inference 2x más lento | Trade-off no justificado |

### Best Practices
- **Chunk size**: 2500 palabras (75% de context window, deja margen para prompt)
- **Overlap**: 200 palabras (8% de chunk, captura contexto sin redundancia excesiva)
- **Boundary detection**: Usar `\n\n` (paragraph breaks) como puntos de corte preferidos
- **Deduplication threshold**: 90% similaridad (permite variaciones menores de redacción)
- **Logging**: Registrar número de chunks procesados en metadata (para debug)

### Code Example
```python
def chunk_text(text: str, chunk_size: int = 2500, overlap: int = 200) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def consolidate_analyses(partial_analyses: list[Analisis]) -> Analisis:
    # Unión de listas
    all_partes = [p for a in partial_analyses for p in a.partes]
    # Deduplicación fuzzy
    unique_partes = deduplicate_fuzzy(all_partes, threshold=0.9)
    # ... similar para otras categorías
    # Recortar resumen a 10 bullets más informativos
    all_bullets = [b for a in partial_analyses for b in a.resumen_bullets]
    top_bullets = select_top_bullets(all_bullets, n=10)  # TF-IDF scoring
    # Promedio de confianza
    avg_confianza = sum(a.confianza_aprox for a in partial_analyses) / len(partial_analyses)
    return Analisis(partes=unique_partes, resumen_bullets=top_bullets, confianza_aprox=avg_confianza, ...)
```

### References
- [Handling Long Documents with LLMs](https://blog.langchain.dev/long-context-challenges/)
- [Text Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/)

---

## Summary of Technology Stack

### Core Technologies (Finalized)

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| **Language** | Python | 3.10+ | ML ecosystem, Streamlit, Ollama bindings |
| **UI Framework** | Streamlit | 1.30+ | Rapid prototyping, zero frontend code |
| **PDF Native** | pdfplumber | 0.10+ | Balance extraction/layout |
| **DOCX** | python-docx | 1.1+ | Standard de facto |
| **OCR** | Tesseract 5 + pytesseract | 0.3.10+ | Open-source, 100+ languages |
| **PDF to Image** | pdf2image | 1.16+ | Poppler wrapper, fast |
| **Local LLM** | Ollama + llama3.2:3b | latest | Balanced quality/resources |
| **Data Validation** | Pydantic | 2.5+ | Type-safe, auto-serialization |
| **Persistence (MVP)** | JSON file | N/A | Zero setup, human-readable |
| **Persistence (Fase 2)** | SQLite + SQLModel | latest | Queries, transactions ACID |

### Deployment Requirements

**System Prerequisites**:
- Python 3.10+ runtime
- Tesseract OCR binary installed
- Ollama service running locally (localhost:11434)
- 4GB+ RAM (8GB recommended)
- 2GB+ disk space (models + documents cache)

**Python Dependencies** (requirements.txt):
```
streamlit==1.30.0
pdfplumber==0.10.3
python-docx==1.1.0
pdf2image==1.16.3
pytesseract==0.3.10
pillow==10.1.0
pydantic==2.5.0
requests==2.31.0
```

**Optional Dependencies**:
- `sqlmodel` (Fase 2 SQLite migration)
- `pytest` + `pytest-cov` (testing)
- `mypy` (static type checking)
- `black` + `ruff` (formatting + linting)

---

## Open Questions & Future Research

### Resolved ✅
- [x] Qué lenguaje usar → **Python 3.10+**
- [x] Qué UI framework → **Streamlit**
- [x] Qué LLM local → **Ollama + llama3.2:3b**
- [x] Qué OCR engine → **Tesseract 5**
- [x] Cómo persistir historial → **JSON file (MVP)**
- [x] Cómo manejar documentos largos → **Chunking + consolidación**

### Pending ⏳ (Fase 2+)
- [ ] ¿Cuándo migrar a SQLite? (Cuando historial >500 duplas o se requieran queries complejas)
- [ ] ¿Agregar soporte de modelos más grandes (mistral:7b) como opción? (Si HW de usuarios lo permite)
- [ ] ¿Implementar análisis comparativo (diff entre 2 duplas)? (Feature request común esperada)
- [ ] ¿Soportar extracción de tablas complejas con Camelot? (Si contratos con tablas financieras complejas)
- [ ] ¿Traducción automática de documentos multilenguaje? (Si casos de uso internacionales)

---

**Research Phase Status**: ✅ **COMPLETE** - All critical decisions finalized, proceed to Phase 1 (Design)
