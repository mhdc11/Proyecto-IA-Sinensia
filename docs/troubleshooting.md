# 🔧 Guía de Troubleshooting

Soluciones para problemas comunes del Analizador de Documentos Legales.

---

## 🚨 Problemas Críticos

### 1. Ollama No Conecta

**Síntoma:**
```
❌ Ollama: Desconectado
Error: Connection refused to localhost:11434
```

**Causas:**
- Ollama no está corriendo
- Puerto 11434 bloqueado
- Modelo no descargado

**Soluciones:**

1. **Verificar servicio:**
```bash
ollama list
```

Si muestra error, iniciar:
```bash
ollama serve
```

Debe mostrar: `Ollama is running on http://localhost:11434`

2. **Verificar puerto:**
```bash
# Windows
netstat -ano | findstr :11434

# macOS/Linux
lsof -i :11434
```

Si está ocupado, matar proceso o cambiar puerto en `config/ollama_config.yaml`:
```yaml
base_url: "http://localhost:11435"  # Puerto alternativo
```

3. **Descargar modelo:**
```bash
ollama pull llama3.2:3b
```

Verificar:
```bash
ollama list | grep llama3.2
```

**Test rápido:**
```bash
ollama run llama3.2:3b "Hola, ¿funcionas?"
```

---

### 2. OCR de Baja Calidad

**Síntoma:**
```
Texto extraído:
"C0ntr@t0 d3 Tr4b4j0 3ntr3..."  # Caracteres incorrectos
```

**Causas:**
- Documento escaneado con baja resolución
- Tesseract no instalado correctamente
- Idioma OCR incorrecto

**Soluciones:**

1. **Aumentar DPI:**

Editar `config/ocr_config.yaml`:
```yaml
ocr:
  dpi: 400      # Aumentar desde 300
  lang: "spa"
```

Mayor DPI = mejor calidad pero más lento:
- **300 DPI** - Balance (default)
- **400 DPI** - Buena calidad
- **600 DPI** - Máxima calidad (muy lento)

2. **Configurar idioma correcto:**

| Idioma | Código | Instalación |
|--------|--------|-------------|
| Español | `spa` | `tesseract-ocr-spa` |
| Inglés | `eng` | Incluido por defecto |
| Español+Inglés | `spa+eng` | Ambos paquetes |

```bash
# Verificar idiomas instalados
tesseract --list-langs
```

Instalar idiomas faltantes:
```bash
# Linux
sudo apt install tesseract-ocr-spa

# macOS
brew install tesseract-lang

# Windows
# Seleccionar "Spanish" en instalador de Tesseract
```

3. **Preprocesar imagen:**

Si el documento tiene:
- **Fondo gris** → Aplicar binarización
- **Texto inclinado** → Rotar antes de escanear
- **Bordes/ruido** → Recortar imagen

**Script de preprocesamiento:**
```python
from PIL import Image, ImageEnhance

img = Image.open("documento.jpg")
img = img.convert('L')  # Convertir a escala de grises
img = ImageEnhance.Contrast(img).enhance(2.0)  # Aumentar contraste
img.save("documento_procesado.jpg")
```

---

### 3. JSON Inválido del LLM

**Síntoma:**
```
❌ Error analizando documento:
ValidationError: Invalid JSON format
```

**Causas:**
- Temperatura muy alta
- Modelo pequeño (phi3:mini)
- Documento extremadamente complejo

**Soluciones:**

1. **Bajar temperatura:**

Editar `config/ollama_config.yaml`:
```yaml
ollama:
  model: "llama3.2:3b"
  temperature: 0.1  # Bajar desde 0.2
```

Temperatura recomendada por modelo:
- `llama3.2:3b` → 0.1-0.2
- `phi3:mini` → 0.1 (muy determinista)
- `mistral:7b` → 0.1-0.3

2. **Actualizar modelo:**
```bash
ollama pull llama3.2:3b  # Forzar actualización
```

3. **Aumentar reintentos:**

Editar `src/orchestration/analyzer.py`:
```python
MAX_RETRIES = 3  # Aumentar desde 2
```

4. **Revisar prompts:**

Si los prompts están muy largos o confusos:
```bash
# Ver tamaño del prompt
python -c "from src.orchestration.prompts import *; print(f'Tokens aprox: {len(LLM_CONSTITUTION + LLM_SPECIFY + LLM_PLAN) / 4}')"
```

Si > 2000 tokens → Simplificar en `src/orchestration/prompts.py`

---

### 4. Documento Demasiado Largo

**Síntoma:**
```
⏳ Extrayendo...
(tarda > 5 minutos sin progreso)
```

**Causas:**
- Documento > 50 páginas sin chunking
- PDF corrupto con imágenes pesadas
- Memoria insuficiente

**Soluciones:**

1. **Verificar chunking automático:**

El sistema usa chunking automático para textos > 15,000 caracteres.

Verificar en logs:
```
[CHUNKER] Texto largo detectado: 45,234 caracteres
[CHUNKER] Dividiendo en 4 chunks...
```

Si no aparece, activar manualmente en `src/orchestration/chunker.py`:
```python
MAX_CHUNK_SIZE = 12000  # Reducir desde 15000
```

2. **Reducir tamaño del PDF:**

```bash
# Linux/macOS con Ghostscript
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=documento_comprimido.pdf documento_original.pdf
```

3. **Dividir documento:**

Si > 100 páginas, dividir en partes:
- Parte 1: Páginas 1-50
- Parte 2: Páginas 51-100
- Analizar por separado

---

## ⚠️ Advertencias y Errores Comunes

### Advertencia: "Análisis con advertencias"

**Significado:**
El análisis se completó pero algunas categorías tienen baja confianza o están incompletas.

**Acciones:**
1. Revisar categoría "Notas" para detalles
2. Verificar campo `confianza_aprox` (< 0.7 = sospechoso)
3. Contrastar con documento original

**No es un error crítico**, solo una señal de precaución.

---

### Error: "Archivo demasiado grande (>100MB)"

**Causa:**
Límite de tamaño configurado para evitar consumir toda la RAM.

**Solución:**

Aumentar límite (con precaución):
```python
# src/ui/components/file_uploader.py
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200MB
```

**Alternativa recomendada:**
Comprimir PDF o dividir en partes.

---

### Error: "No se pudo extraer texto del PDF"

**Causas:**
- PDF corrupto
- PDF protegido con contraseña
- PDF puramente gráfico (sin capa de texto)

**Solución:**

1. **Verificar integridad:**
```bash
# Windows
magick identify documento.pdf

# Linux/macOS
pdfinfo documento.pdf
```

Si muestra error → PDF corrupto, intentar reparar con Adobe Acrobat o herramientas online.

2. **PDF protegido:**
Desbloquear antes de analizar (requiere contraseña).

3. **PDF gráfico:**
El OCR debería activarse automáticamente. Si no:

Forzar OCR manualmente en código:
```python
# Llamar directamente al extractor OCR
from src.extraction.pdf_ocr import extract_pdf_ocr
texto, paginas = extract_pdf_ocr("documento.pdf", dpi=400, lang="spa")
```

---

## 🐌 Problemas de Rendimiento

### Análisis Muy Lento

**Síntoma:**
PDF de 10 páginas tarda > 2 minutos.

**Causas:**
- Hardware limitado
- Modelo grande (mistral:7b)
- OCR en alta resolución

**Soluciones:**

1. **Usar modelo más ligero:**
```bash
ollama pull phi3:mini  # Solo 2GB RAM
```

Editar `config/ollama_config.yaml`:
```yaml
model: "phi3:mini"
```

2. **Reducir DPI del OCR:**
```yaml
ocr:
  dpi: 200  # Desde 300
```

3. **Deshabilitar chunking para docs cortos:**
```python
# src/orchestration/chunker.py
MAX_CHUNK_SIZE = 20000  # Aumentar umbral
```

4. **Hardware:**
- Cerrar aplicaciones pesadas
- Usar GPU si disponible (Ollama detecta automáticamente)

---

### Memoria Insuficiente

**Síntoma:**
```
MemoryError: Unable to allocate array
```

**Soluciones:**

1. **Cerrar otros programas**

2. **Usar modelo más pequeño:**
```bash
ollama pull phi3:mini
```

3. **Reducir max_tokens:**
```yaml
ollama:
  max_tokens: 2000  # Desde 4000
```

---

## 🔍 Debugging Avanzado

### Activar Logs Detallados

Editar `config/logging_config.yaml`:
```yaml
logging:
  level: DEBUG  # Desde INFO
  handlers:
    file:
      enabled: true
      path: "logs/app.log"
```

Reiniciar aplicación. Los logs aparecerán en `logs/app.log`.

### Inspeccionar Respuesta del LLM

```python
# Añadir en src/orchestration/analyzer.py tras llamar a Ollama
print(f"[DEBUG] Respuesta LLM:\n{llm_response}")
```

Buscar:
- Texto antes/después del JSON
- JSON malformado (comas, llaves)
- Campos faltantes

---

## 📞 Soporte Adicional

Si el problema persiste:

1. **Revisar logs:** `logs/app.log` (si está activado)
2. **Test de componentes:**
```bash
# Test extracción
python -m src.extraction.auto_extractor documento.pdf

# Test Ollama
ollama run llama3.2:3b "Test"

# Test OCR
tesseract documento.jpg salida.txt -l spa
```

3. **Crear issue:** Incluir:
   - Versión de Python, Ollama, Tesseract
   - Tipo de documento (PDF nativo/escaneado, páginas, tamaño)
   - Logs relevantes
   - Pasos para reproducir

---

**¿Algo no está cubierto aquí?** Consulta [README.md](../README.md) o [docs/prompts.md](prompts.md) para más información.
