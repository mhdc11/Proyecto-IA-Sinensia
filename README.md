# Analizador de Documentos Legales 📄

**Versión**: 1.0.0-MVP | **Estado**: En Desarrollo | **Licencia**: MIT

## Descripción

Sistema de análisis local de documentos legales, laborales y administrativos que extrae puntos clave mediante IA local (Ollama), procesando PDF (nativos y escaneados), DOCX e imágenes con OCR. Presenta resultados estructurados en 8 categorías, mantiene historial persistente y exporta resultados en JSON.

### Características Principales

- ✅ **100% Local y Privado**: Sin envío de datos a servicios externos
- ✅ **Múltiples Formatos**: PDF (nativos/escaneados), DOCX, imágenes (PNG/JPG/TIFF)
- ✅ **8 Categorías Estructuradas**: Partes, Fechas, Importes, Obligaciones, Derechos, Riesgos, Resumen, Tipo
- ✅ **Historial Navegable**: Sistema de "duplas" (documento ↔ análisis)
- ✅ **Exportación**: Resultados en formato JSON
- ✅ **OCR Integrado**: Procesamiento de documentos escaneados con Tesseract
- ✅ **IA Local**: Análisis con Ollama (llama3.2:3b) sin conexión a internet

## Requisitos del Sistema

### Hardware Mínimo

- **CPU**: Dual-core (últimos 5 años)
- **RAM**: 4GB (8GB recomendado)
- **Disco**: 4GB libres (2GB para modelos IA + 2GB para documentos)
- **GPU**: Opcional (acelera el análisis con IA)

### Software Necesario

1. **Python 3.10 o superior**
   ```bash
   python --version  # Debe mostrar 3.10+
   ```

2. **Tesseract OCR** (para documentos escaneados)
   - **Windows**: [Descargar installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-spa`

3. **Ollama** (motor de IA local)
   - Descargar: [ollama.com/download](https://ollama.com/download)
   - Verificar: `ollama --version`

## Instalación Rápida (5 minutos)

### Paso 1: Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd proyectoPersonal
```

### Paso 2: Crear Entorno Virtual

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

Verás `(venv)` al inicio de tu terminal cuando esté activado.

### Paso 3: Instalar Dependencias Python

```bash
pip install -r requirements.txt
```

### Paso 4: Descargar Modelo de IA Local

```bash
ollama pull llama3.2:3b
```

Esto descarga ~2GB. Si tienes hardware limitado:
```bash
ollama pull phi3:mini  # Solo 1GB, menor calidad
```

### Paso 5: Iniciar Ollama

**Dejar esta terminal abierta**:
```bash
ollama serve
```

Debe mostrar: `Ollama is running on http://localhost:11434`

### Paso 6: Iniciar la Aplicación

En una **nueva terminal** (con el entorno virtual activado):

```bash
streamlit run src/ui/app.py
```

Debe abrir automáticamente tu navegador en **http://localhost:8501**

## Uso Básico

### 1. Cargar Documentos

1. Haz clic en **"Seleccionar archivos"** en la interfaz
2. Elige uno o varios documentos (PDF/DOCX/Imágenes)
3. Máximo 100MB por archivo

### 2. Esperar Análisis

- **PDF nativo (10 páginas)**: ~20-30 segundos
- **PDF escaneado (5 páginas)**: ~40-60 segundos (OCR + análisis)

### 3. Ver Resultados

Los resultados aparecen en **tarjetas organizadas por categorías**:

- **Partes Involucradas**
- **Fechas Relevantes**
- **Importes y Datos Económicos**
- **Obligaciones**
- **Derechos**
- **Riesgos y Alertas**
- **Resumen Ejecutivo**
- **Tipo de Documento**

### 4. Navegar Historial

La **barra lateral izquierda** muestra todos los análisis previos.

### 5. Exportar Resultados

Haz clic en **"Exportar JSON"** para guardar el análisis.

## Estructura del Proyecto

```
proyectoPersonal/
├── src/
│   ├── models/          # Esquemas Pydantic (Documento, Análisis, Dupla)
│   ├── extractors/      # Extracción de texto (PDF, DOCX, OCR)
│   ├── orchestration/   # Pipeline de análisis y cliente Ollama
│   ├── persistence/     # Almacenamiento local (JSON/SQLite)
│   ├── ui/              # Interfaz Streamlit
│   └── utils/           # Utilidades (hashing, logging, normalización)
├── tests/
│   ├── unit/            # Tests unitarios
│   ├── integration/     # Tests end-to-end
│   └── fixtures/        # Documentos de prueba
├── data/                # Almacenamiento local (duplas.json)
├── config/              # Configuración (Ollama, Streamlit, logging)
├── docs/                # Documentación técnica
└── requirements.txt     # Dependencias Python
```

## Privacidad y Seguridad

### 🔒 Garantías de Privacidad

✅ **100% Local**: Todo el procesamiento ocurre en tu equipo
- OCR local (Tesseract)
- IA local (Ollama)
- Almacenamiento local (archivo JSON en tu disco)

✅ **Sin Internet**: La aplicación funciona offline completamente

✅ **Sin Telemetría**: No se envía ningún dato a servidores externos

✅ **Control Total**: Tú decides qué se guarda y cuándo se elimina

### ⚠️ Recomendaciones de Seguridad

1. **No compartir pantalla** mientras analizas documentos sensibles
2. **Eliminar análisis** de documentos temporales tras revisarlos
3. **Backup regular** del historial (`data/duplas.json`)
4. **No exponer** la aplicación a internet (solo localhost:8501)

## Tecnologías

- **Backend**: Python 3.10+
- **UI**: Streamlit 1.30+
- **Text Extraction**: pdfplumber, python-docx, pytesseract
- **OCR**: Tesseract + pdf2image
- **AI**: Ollama (llama3.2:3b)
- **Data Validation**: Pydantic 2.5+
- **Storage**: JSON (migración a SQLite planeada)
- **Testing**: pytest 7.4+

## Documentación Adicional

- **Instalación Detallada**: Ver `docs/deployment.md`
- **Arquitectura**: Ver `docs/architecture.md`
- **Prompts del LLM**: Ver `docs/prompts.md`
- **Troubleshooting**: Ver `docs/troubleshooting.md`
- **Guía Rápida**: Ver `specs/001-doc-analyzer/quickstart.md`

## Desarrollo

### Ejecutar Tests

```bash
pytest tests/ -v
```

### Cobertura de Código

```bash
pytest --cov=src tests/
```

### Linting y Formato

```bash
# Flake8 (linting)
flake8 src/ tests/

# Black (auto-formatting)
black src/ tests/

# mypy (type checking)
mypy src/
```

## Contribución

Este proyecto sigue el framework **SpecKit** para desarrollo estructurado:

1. **Especificación**: `/speckit.specify` - Define qué hace el sistema
2. **Planificación**: `/speckit.plan` - Diseño técnico
3. **Tareas**: `/speckit.tasks` - Desglose de implementación
4. **Implementación**: `/speckit.implement` - Ejecución

Ver `specs/001-doc-analyzer/` para detalles de diseño.

## Licencia

MIT License - Ver archivo `LICENSE` para detalles.

## Soporte

### Reportar Problemas

Si encuentras un error:

1. Anotar pasos exactos para reproducir
2. Incluir tipo de documento (PDF nativo/escaneado, DOCX, etc.)
3. Revisar logs en terminal
4. Crear issue en el repositorio

**Importante**: NO incluir documentos sensibles reales. Anonimizar o usar documentos de ejemplo.

## FAQ

**P: ¿Cuánto tarda en analizar un documento?**
R: PDF nativo 10 páginas: 20-30 seg | PDF escaneado 5 páginas: 40-60 seg

**P: ¿Puedo usar la aplicación offline?**
R: Sí, 100%. Funciona sin internet una vez instalado.

**P: ¿Los datos se guardan en la nube?**
R: No. Todo se guarda en tu disco local (`data/duplas.json`).

**P: ¿El análisis es perfecto?**
R: No. La IA local puede cometer errores. Siempre verifica información crítica contra el documento original.

**P: ¿Puedo usar esta herramienta para asesoramiento legal?**
R: **NO**. La aplicación SOLO extrae y resume información. Consulta un abogado para decisiones importantes.

---

**¡Listo para empezar! 🚀**

Carga tu primer documento y en menos de un minuto tendrás un análisis estructurado completo.
