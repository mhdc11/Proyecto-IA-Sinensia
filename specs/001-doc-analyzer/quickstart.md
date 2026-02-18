# Quickstart Guide: Analizador de Documentos Legales

**Feature**: 001-doc-analyzer
**Date**: 2026-02-18
**For**: End Users

---

## Overview

Esta aplicación te permite analizar documentos legales, laborales y administrativos de forma **100% local** (sin enviar nada a internet), extrayendo automáticamente:

- **Partes involucradas** (empresas, personas, identificadores)
- **Fechas relevantes** (inicio, fin, plazos, vencimientos)
- **Importes** (salarios, indemnizaciones, bonificaciones)
- **Obligaciones** (deberes y compromisos)
- **Derechos** (facultades y beneficios)
- **Riesgos** (cláusulas sensibles, penalizaciones, confidencialidad)
- **Resumen ejecutivo** (5-10 puntos clave)

Mantiene un **historial navegable** de todos los análisis realizados y permite **exportar resultados** en formato JSON.

---

## Requisitos del Sistema

### Hardware Mínimo

- **CPU**: Dual-core (últimos 5 años)
- **RAM**: 4GB (8GB recomendado)
- **Disco**: 4GB libres (2GB para modelos IA + 2GB para documentos)
- **GPU**: Opcional (acelera el análisis con IA)

### Software Necesario

1. **Python 3.10 o superior**
   - Verificar: `python --version` debe mostrar 3.10+
   - Descargar: [python.org/downloads](https://www.python.org/downloads/)

2. **Tesseract OCR** (para documentos escaneados)
   - **Windows**: Descargar [installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-spa`
   - Verificar: `tesseract --version`

3. **Ollama** (motor de IA local)
   - Descargar: [ollama.com/download](https://ollama.com/download)
   - Verificar: `ollama --version`

---

## Instalación Rápida (5 minutos)

### Paso 1: Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd <nombre-del-repositorio>
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

Esto instalará:
- Streamlit (interfaz web)
- pdfplumber (lectura de PDFs)
- python-docx (lectura de DOCX)
- pytesseract (OCR para escaneos)
- pydantic (validación de datos)
- requests (comunicación con Ollama)

### Paso 4: Descargar Modelo de IA Local

```bash
ollama pull llama3.2:3b
```

Esto descarga ~2GB. Si tienes hardware limitado, puedes usar un modelo más ligero:
```bash
ollama pull phi3:mini  # Solo 1GB, pero menor calidad de análisis
```

### Paso 5: Iniciar Ollama

**Dejar esta terminal abierta**:
```bash
ollama serve
```

Debe mostrar: `Ollama is running on http://localhost:11434`

Si ya está corriendo como servicio, puedes omitir este paso.

### Paso 6: Iniciar la Aplicación

En una **nueva terminal** (con el entorno virtual activado):

```bash
streamlit run src/ui/app.py
```

Debe abrir automáticamente tu navegador en **http://localhost:8501**

Si no abre, copia la URL manualmente del output de la terminal.

---

## Uso Básico

### 1. Cargar Documentos

1. Haz clic en **"Seleccionar archivos"** en la interfaz
2. Elige uno o varios documentos:
   - ✅ PDFs (nativos o escaneados)
   - ✅ DOCX
   - ✅ Imágenes (PNG, JPG, TIFF)
3. Máximo 100MB por archivo

### 2. Esperar Análisis

- **PDF nativo (10 páginas)**: ~20-30 segundos
- **PDF escaneado (5 páginas)**: ~40-60 segundos (OCR + análisis)
- **DOCX (5 páginas)**: ~15-25 segundos

Verás indicadores de progreso:
- "Extrayendo texto de contrato.pdf..."
- "OCR en progreso (página 3/5)..."
- "Analizando con IA local..."

### 3. Ver Resultados

Los resultados aparecen en **tarjetas organizadas por categorías**:

- **Partes Involucradas**: Empresas, personas, identificadores (CIF/NIF)
- **Fechas Relevantes**: Inicio, fin, plazos (formato legible)
- **Importes y Datos Económicos**: Salarios, indemnizaciones, monedas
- **Obligaciones**: Deberes y compromisos (bullets)
- **Derechos**: Facultades y beneficios (bullets)
- **Riesgos y Alertas**: Cláusulas sensibles destacadas ⚠️
- **Resumen Ejecutivo**: 5-10 puntos clave del documento

### 4. Navegar Historial

La **barra lateral izquierda** muestra todos los análisis previos:

- 📄 Nombre del documento
- 📋 Tipo de documento (contrato, nómina, convenio...)
- 📅 Fecha de análisis
- ✅/⚠️ Estado (válido, con advertencias, incompleto)

Haz clic en cualquier entrada para recuperar su análisis.

### 5. Eliminar Entradas

1. Selecciona una dupla del historial
2. Haz clic en **"Eliminar análisis"**
3. Confirma la acción (⚠️ no se puede deshacer)

### 6. Exportar Resultados

Haz clic en **"Exportar JSON"** para guardar el análisis:

```json
{
  "documento": {
    "nombre": "contrato-laboral-2024.pdf",
    "tipo_fuente": "pdf_native",
    "paginas": 12,
    ...
  },
  "analisis": {
    "tipo_documento": "contrato_laboral",
    "partes": ["Empresa X", "Juan Pérez"],
    "fechas": [...],
    "importes": [...],
    "obligaciones": [...],
    "derechos": [...],
    "riesgos": [...],
    "resumen_bullets": [...],
    "confianza_aprox": 0.9
  }
}
```

El archivo se guarda en tu carpeta de descargas.

---

## Solución de Problemas

### Error: "Ollama no está ejecutándose"

**Síntoma**: Badge rojo 🔴 "Ollama offline" en la interfaz

**Solución**:
1. Verificar que Ollama está corriendo: `ollama list` en terminal
2. Si no está corriendo: `ollama serve` en terminal separada
3. Refrescar la aplicación web (F5)

### Error: "Tesseract no encontrado"

**Síntoma**: Falla al procesar documentos escaneados

**Solución**:
1. **Windows**: Instalar desde [aquí](https://github.com/UB-Mannheim/tesseract/wiki) y añadir a PATH
2. **macOS**: `brew install tesseract`
3. **Linux**: `sudo apt install tesseract-ocr`
4. Reiniciar terminal y aplicación

### Error: "Archivo demasiado grande"

**Síntoma**: "Archivo excede límite de 100MB"

**Solución**:
1. Comprimir el PDF (herramientas online: smallpdf.com)
2. Dividir el documento en partes más pequeñas
3. Si es imagen: reducir resolución a 300 DPI

### Análisis Muy Lento

**Síntoma**: >2 minutos por documento de 10 páginas

**Posibles Causas**:
1. CPU viejo o sobrecargado → cerrar otras aplicaciones
2. Modelo muy pesado → cambiar a `phi3:mini` (más ligero)
3. Documento escaneado de baja calidad → requiere más tiempo de OCR

**Optimizaciones**:
```bash
# Cambiar a modelo más ligero (sacrifica algo de calidad)
ollama pull phi3:mini

# Luego editar src/ui/app.py línea ~15:
MODEL_NAME = "phi3:mini"  # en lugar de "llama3.2:3b"
```

### OCR Produce Texto Ilegible

**Síntoma**: Análisis con muchas categorías vacías, `confianza_aprox < 0.5`

**Causas**:
- Documento escaneado de muy baja calidad
- Imagen borrosa o con sombras
- Texto manuscrito (OCR no soportado)

**Soluciones**:
1. Re-escanear documento a 300-400 DPI
2. Mejorar contraste de la imagen (herramientas de edición)
3. Si es manuscrito, transcribir manualmente a texto antes de analizar

### Análisis Incompleto (Categorías Vacías)

**Síntoma**: `estado: "incompleto"`, muchas categorías con "No disponible"

**Posibles Razones (NORMALES)**:
- El documento realmente no contiene esa información
  - Ejemplo: Un recibo simple no tiene "fechas de vencimiento"
- Documento muy breve (1-2 páginas con poco contenido)

**Esto NO es un error** si el documento carece de esa información.

Si el documento SÍ tiene información pero no se detecta:
1. Verificar que el texto extraído es legible (ver logs)
2. Reportar como issue con documento de ejemplo (anonimizado)

---

## Documentos Soportados

### Formatos Compatibles

| Formato | Soporte | Notas |
|---------|---------|-------|
| **PDF nativo** | ✅ Excelente | Texto embebido, extracción directa |
| **PDF escaneado** | ✅ Bueno | Requiere OCR (más lento) |
| **DOCX** | ✅ Excelente | Microsoft Word 2007+ |
| **DOC** | ❌ No | Convertir a DOCX antes |
| **PNG/JPG** | ✅ Bueno | Imágenes de documentos con OCR |
| **TIFF** | ✅ Bueno | Común en escaneos profesionales |
| **TXT** | ⚠️ Limitado | Texto plano sin estructura |
| **RTF** | ❌ No | Conversión futura planeada |

### Límites

- **Tamaño máximo**: 100MB por archivo
- **Páginas máximas**: 500 (rendimiento óptimo hasta 50)
- **Idiomas**: Español (primario), Inglés (secundario)
- **OCR**: Español, Inglés, Catalán, Gallego, Euskera

---

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
3. **Backup regular** del historial (`data/duplas.json`) si es información crítica
4. **No exponer** la aplicación a internet (solo localhost:8501)

---

## Próximos Pasos

### Funcionalidades Disponibles

- ✅ Análisis individual de documentos
- ✅ Análisis batch (múltiples documentos)
- ✅ Historial persistente de duplas
- ✅ Exportación JSON
- ✅ Eliminación de entradas

### Funcionalidades Futuras (Roadmap)

- ⏳ Análisis comparativo (diff entre 2 documentos)
- ⏳ Filtrado avanzado del historial (por tipo, fecha, partes)
- ⏳ Exportación a Excel/CSV
- ⏳ Etiquetado manual de documentos
- ⏳ Búsqueda full-text en historial
- ⏳ Soporte de más idiomas (francés, alemán)

---

## Soporte

### Documentación Adicional

- **Documentación técnica**: Ver `specs/001-doc-analyzer/plan.md`
- **Modelo de datos**: Ver `specs/001-doc-analyzer/data-model.md`
- **API de Ollama**: Ver `specs/001-doc-analyzer/contracts/ollama-prompt.md`

### Reportar Problemas

Si encuentras un error o comportamiento inesperado:

1. Anotar pasos exactos para reproducir el problema
2. Incluir tipo de documento (PDF nativo/escaneado, DOCX, etc.)
3. Revisar logs en terminal (buscar errores en rojo)
4. Crear issue en el repositorio con:
   - Descripción del problema
   - Logs relevantes
   - Versión de Python y Ollama
   - Sistema operativo

**Importante**: NO incluir documentos sensibles reales en los reportes. Anonimizar o usar documentos de ejemplo.

---

## FAQ

**P: ¿Cuánto tarda en analizar un documento?**
R: Depende del tamaño y tipo:
- PDF nativo 10 páginas: 20-30 seg
- PDF escaneado 5 páginas: 40-60 seg (OCR lento)
- DOCX 5 páginas: 15-25 seg

**P: ¿Puedo usar la aplicación offline?**
R: Sí, 100%. Una vez instalado todo (Python, Tesseract, Ollama + modelo), funciona sin internet.

**P: ¿Cuántos documentos puedo almacenar?**
R: Hasta ~1000 análisis sin degradación de rendimiento. Después, considera limpiar el historial o migrar a SQLite (futura versión).

**P: ¿El análisis es perfecto?**
R: No. La IA local puede cometer errores, especialmente con:
- Documentos muy complejos o mal redactados
- OCR de baja calidad
- Abreviaturas o jerga específica
Siempre verifica información crítica contra el documento original.

**P: ¿Puedo usar esta herramienta para asesoramiento legal?**
R: **NO**. La aplicación SOLO extrae y resume información. No interpreta cláusulas ni ofrece conclusiones legales. Consulta un abogado para decisiones importantes.

**P: ¿Los datos se guardan en la nube?**
R: No. Todo se guarda en tu disco local (`data/duplas.json`). Nada se envía a internet.

**P: ¿Funciona en móviles/tablets?**
R: No directamente. Requiere Python, Tesseract y Ollama que son aplicaciones de escritorio. Uso en navegador móvil posible si el servidor corre en PC local, pero no recomendado (UI no optimizada).

---

**¡Listo para empezar! 🚀**

Carga tu primer documento y en menos de un minuto tendrás un análisis estructurado completo.
