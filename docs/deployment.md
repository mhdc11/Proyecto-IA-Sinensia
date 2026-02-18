# Guía de Despliegue: Analizador de Documentos Legales

**Última actualización**: 2026-02-18 | **Versión**: 1.0.0-MVP

---

## Requisitos Previos

### 1. Python 3.10 o Superior

**Verificación**:
```bash
python --version  # Debe mostrar 3.10 o superior
```

**Instalación**:
- **Windows**: Descargar desde [python.org/downloads](https://www.python.org/downloads/)
- **macOS**: `brew install python@3.10` o descargar desde python.org
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update
  sudo apt install python3.10 python3.10-venv python3-pip
  ```

---

## 2. Tesseract OCR (Para Documentos Escaneados)

Tesseract es necesario para procesar documentos escaneados mediante OCR (Optical Character Recognition).

### Windows

1. **Descargar el instalador**:
   - Ir a: [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
   - Descargar la versión más reciente de 64-bit: `tesseract-ocr-w64-setup-vX.X.X.exe`

2. **Instalar**:
   - Ejecutar el instalador
   - **IMPORTANTE**: Durante la instalación, asegurarse de seleccionar:
     - ✅ "Additional language data (download)" → Seleccionar **Spanish** (spa)
     - ✅ Anotar la ruta de instalación (por defecto: `C:\Program Files\Tesseract-OCR`)

3. **Añadir a PATH**:
   - Abrir "Variables de entorno del sistema"
   - Editar la variable `Path` y añadir: `C:\Program Files\Tesseract-OCR`
   - **Reiniciar la terminal** después de este cambio

4. **Verificar instalación**:
   ```bash
   tesseract --version
   # Debe mostrar: tesseract 5.x.x

   tesseract --list-langs
   # Debe incluir: spa (Spanish)
   ```

### macOS

1. **Instalar con Homebrew**:
   ```bash
   brew install tesseract
   brew install tesseract-lang  # Paquete de idiomas adicionales
   ```

2. **Verificar instalación**:
   ```bash
   tesseract --version
   tesseract --list-langs  # Debe incluir 'spa'
   ```

3. **Si no se instaló español**:
   ```bash
   brew install tesseract-lang
   ```

### Linux (Ubuntu/Debian)

1. **Instalar Tesseract y paquete de idioma español**:
   ```bash
   sudo apt update
   sudo apt install tesseract-ocr tesseract-ocr-spa
   ```

2. **Verificar instalación**:
   ```bash
   tesseract --version
   tesseract --list-langs  # Debe incluir 'spa'
   ```

3. **Instalar idiomas adicionales (opcional)**:
   ```bash
   sudo apt install tesseract-ocr-eng  # Inglés
   sudo apt install tesseract-ocr-cat  # Catalán
   sudo apt install tesseract-ocr-glg  # Gallego
   sudo apt install tesseract-ocr-eus  # Euskera
   ```

---

## 3. Poppler (Para Convertir PDF a Imágenes en OCR)

Poppler es una dependencia de `pdf2image` que convierte páginas de PDF a imágenes para procesamiento OCR.

### Windows

1. **Descargar Poppler precompilado**:
   - Ir a: [github.com/oschwartz10612/poppler-windows/releases](https://github.com/oschwartz10612/poppler-windows/releases)
   - Descargar el archivo `.zip` más reciente (ejemplo: `Release-24.02.0-0.zip`)

2. **Extraer**:
   - Extraer el contenido a una carpeta permanente (ejemplo: `C:\Program Files\poppler`)

3. **Añadir a PATH**:
   - Añadir la ruta `C:\Program Files\poppler\Library\bin` a las variables de entorno PATH
   - **Reiniciar la terminal**

4. **Verificar instalación**:
   ```bash
   pdftoppm -v
   # Debe mostrar: pdftoppm version X.X.X
   ```

### macOS

1. **Instalar con Homebrew**:
   ```bash
   brew install poppler
   ```

2. **Verificar instalación**:
   ```bash
   pdftoppm -v
   ```

### Linux (Ubuntu/Debian)

1. **Instalar Poppler**:
   ```bash
   sudo apt install poppler-utils
   ```

2. **Verificar instalación**:
   ```bash
   pdftoppm -v
   ```

---

## 4. Ollama (Motor de IA Local)

Ollama es el motor de IA local que analiza los documentos. **No requiere conexión a internet una vez instalado**.

### Todas las Plataformas

1. **Descargar Ollama**:
   - Ir a: [ollama.com/download](https://ollama.com/download)
   - Descargar el instalador para tu sistema operativo

2. **Instalar**:
   - **Windows**: Ejecutar el instalador `.exe`
   - **macOS**: Abrir el archivo `.dmg` y arrastrar Ollama a Aplicaciones
   - **Linux**:
     ```bash
     curl -fsSL https://ollama.com/install.sh | sh
     ```

3. **Verificar instalación**:
   ```bash
   ollama --version
   # Debe mostrar: ollama version X.X.X
   ```

4. **Iniciar el servicio de Ollama**:

   **En una terminal separada** (dejar ejecutándose):
   ```bash
   ollama serve
   ```

   Debe mostrar:
   ```
   Listening on 127.0.0.1:11434
   ```

5. **Descargar el modelo de IA** (en otra terminal):

   **Modelo recomendado** (equilibrio calidad/recursos):
   ```bash
   ollama pull llama3.2:3b
   ```

   Esto descarga ~2GB. Esperar a que complete.

   **Alternativas según hardware**:
   - Hardware limitado (4GB RAM):
     ```bash
     ollama pull phi3:mini  # Solo 1GB, menor calidad de análisis
     ```

   - Hardware potente (16GB+ RAM, GPU):
     ```bash
     ollama pull mistral:7b  # Mejor calidad, requiere más recursos
     ```

6. **Verificar que el modelo está disponible**:
   ```bash
   ollama list
   # Debe mostrar el modelo descargado (llama3.2:3b o el que hayas elegido)
   ```

7. **Probar el modelo** (opcional):
   ```bash
   ollama run llama3.2:3b "Hola, ¿cómo estás?"
   # Debe responder en español
   ```

8. **Health Check desde Python** (opcional):
   ```bash
   curl http://localhost:11434/api/version
   # Debe retornar JSON con la versión de Ollama
   ```

---

## 5. Instalación del Proyecto

Una vez completados los pasos anteriores:

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

### Paso 3: Instalar Dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Posibles errores y soluciones**:

- **Error**: `pytesseract no encuentra tesseract.exe`
  - **Solución Windows**: Añadir manualmente la ruta en código:
    ```python
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```

- **Error**: `pdf2image no encuentra poppler`
  - **Solución Windows**: Especificar ruta de poppler al llamar `pdf2image`:
    ```python
    from pdf2image import convert_from_path
    images = convert_from_path('file.pdf', poppler_path=r'C:\Program Files\poppler\Library\bin')
    ```

---

## 6. Iniciar la Aplicación

### Paso 1: Asegurarse de que Ollama está ejecutándose

En una terminal separada:
```bash
ollama serve
```

### Paso 2: Ejecutar la aplicación Streamlit

```bash
streamlit run src/ui/app.py
```

La aplicación debe abrir automáticamente en tu navegador en:
```
http://localhost:8501
```

---

## Verificación de Instalación Completa

Lista de verificación:

- [ ] `python --version` muestra 3.10 o superior
- [ ] `tesseract --version` muestra versión 5.x
- [ ] `tesseract --list-langs` incluye "spa"
- [ ] `pdftoppm -v` muestra versión de Poppler
- [ ] `ollama --version` muestra versión de Ollama
- [ ] `ollama list` muestra el modelo descargado (llama3.2:3b)
- [ ] `ollama serve` ejecutándose sin errores
- [ ] `pip install -r requirements.txt` completado sin errores
- [ ] `streamlit run src/ui/app.py` abre la aplicación en el navegador

---

## Troubleshooting

### Problema: Ollama no inicia

**Síntomas**: `ollama serve` falla o badge rojo 🔴 "Ollama offline" en UI

**Soluciones**:
1. Verificar que el puerto 11434 no esté ocupado:
   ```bash
   # Windows
   netstat -ano | findstr :11434

   # macOS/Linux
   lsof -i :11434
   ```

2. Matar procesos de Ollama y reiniciar:
   ```bash
   # Windows
   taskkill /F /IM ollama.exe

   # macOS/Linux
   pkill ollama

   # Luego reiniciar
   ollama serve
   ```

### Problema: Tesseract no encuentra idioma español

**Síntomas**: Error "Language 'spa' not found"

**Solución**: Descargar manualmente los datos de idioma:
- Windows: Durante reinstalación, seleccionar "Additional language data"
- macOS: `brew reinstall tesseract tesseract-lang`
- Linux: `sudo apt install tesseract-ocr-spa`

### Problema: OCR produce texto ilegible

**Síntomas**: Análisis con muchas categorías vacías, confianza_aprox < 0.5

**Causas posibles**:
- Documento escaneado de muy baja calidad
- Imagen borrosa o con sombras

**Soluciones**:
1. Re-escanear documento a 300-400 DPI
2. Mejorar contraste de la imagen antes de analizar
3. Si es manuscrito, transcribir manualmente (OCR no soporta manuscrito)

---

## Configuración Avanzada

### Cambiar el modelo de Ollama

Editar `config/ollama_config.yaml`:
```yaml
model: "phi3:mini"  # o "mistral:7b"
```

### Ajustar temperatura del LLM

En `config/ollama_config.yaml`:
```yaml
temperature: 0.2  # Valores entre 0.1-0.5 (menor = más determinista)
```

### Cambiar idioma de OCR

En `config/ollama_config.yaml`:
```yaml
ocr_languages: "spa+eng"  # español + inglés
```

---

**¡Instalación completa! 🎉**

Si todos los pasos se completaron exitosamente, ya puedes empezar a analizar documentos.
