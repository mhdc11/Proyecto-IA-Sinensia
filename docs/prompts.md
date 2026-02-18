# 📝 Guía de Prompts Internos

Esta guía explica cómo modificar los prompts internos del sistema para personalizar el comportamiento del análisis con el LLM local (Ollama).

---

## 📂 Ubicación de los Prompts

Los prompts están definidos en: **`src/orchestration/prompts.py`**

Hay tres bloques principales:

1. **LLM_CONSTITUTION** - Reglas generales de comportamiento
2. **LLM_SPECIFY** - Esquema de salida esperado (JSON)
3. **LLM_PLAN** - Pasos internos del análisis

---

## 🔧 Estructura de los Prompts

### 1. LLM_CONSTITUTION

Define las **reglas inmutables** que el LLM debe seguir:

```python
LLM_CONSTITUTION = """
REGLAS FUNDAMENTALES:
1. No inventes datos. Extrae únicamente información presente en el texto.
2. Si una categoría no aparece, devuélvela vacía o con null.
3. Devuelve SIEMPRE un único JSON válido que cumpla el esquema exacto.
4. Salida en español; puedes anotar idioma detectado en "notas" si es útil.
5. No ofrezcas asesoramiento legal. No añadas texto fuera del JSON.
"""
```

**Cuándo modificar:**
- Agregar reglas específicas de tu dominio
- Cambiar idioma de salida por defecto
- Ajustar restricciones de veracidad

**Ejemplo de modificación:**
```python
# Añadir regla para documentos médicos
6. Si el documento contiene información de salud, marca "sensible": true en metadata.
```

### 2. LLM_SPECIFY

Define el **esquema JSON** que el LLM debe generar:

```python
LLM_SPECIFY = """
Dado el contenido textual de un documento, devuelve un JSON con este esquema exacto:
{
  "tipo_documento": "string",
  "partes": ["string"],
  "fechas": [{"etiqueta": "string", "valor": "string"}],
  "importes": [{"concepto": "string", "valor": number|null, "moneda": "string|null"}],
  "obligaciones": ["string"],
  "derechos": ["string"],
  "riesgos": ["string"],
  "resumen_bullets": ["string"],
  "notas": ["string"],
  "confianza_aprox": number
}

Instrucciones:
- Fechas: YYYY-MM-DD cuando sea inequívoco; si no, literal.
- Importes: incluir moneda cuando exista; en otro caso, null.
- Resumen: 5–10 bullets, una idea por bullet.
- Riesgos: cláusulas sensibles (no competencia, penalizaciones, confidencialidad, renuncias).
- Si el texto es escaso/ilegible, reconoce la limitación en "notas".
"""
```

**Cuándo modificar:**
- Añadir nuevas categorías (ej: "ubicaciones", "referencias_legales")
- Cambiar formato de fechas (ISO vs EU)
- Ajustar longitud de resumen (5-10 bullets → 3-7 bullets)

**Ejemplo de modificación:**
```python
# Añadir categoría de ubicaciones
"ubicaciones": ["string"],  # Ciudades, países mencionados
```

### 3. LLM_PLAN

Define los **pasos internos** que el LLM debe seguir:

```python
LLM_PLAN = """
PASOS INTERNOS:
1. Estimar tipo_documento por patrones (contrato, nómina, convenio, anexo, desconocido).
2. Extraer PARTES (nombres/razones sociales, Empresa/Empleador/Trabajador/Empleado, CIF/NIF).
3. Detectar FECHAS (inicio, fin, plazos, vencimientos); normalizar a ISO cuando sea claro.
4. Detectar IMPORTES y su contexto (salario, indemnización, bonus) y moneda.
5. Extraer OBLIGACIONES y DERECHOS a partir de enunciados normativos (frases concisas).
6. Señalar RIESGOS/ALERTAS (no competencia, confidencialidad, penalizaciones, renuncias).
7. Generar RESUMEN (5–10 bullets).
8. Rellenar JSON exactamente como el esquema; nada fuera del JSON.
9. Estimar confianza_aprox por completitud/claridad.
"""
```

**Cuándo modificar:**
- Cambiar orden de prioridades
- Añadir heurísticas específicas (ej: "buscar sellos notariales")
- Ajustar criterios de confianza

---

## ⚙️ Configuración del Modelo Ollama

Ubicación: **`config/ollama_config.yaml`**

```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "llama3.2:3b"
  temperature: 0.2        # 0.1-0.5 recomendado
  max_tokens: 4000
  timeout: 120
```

### Parámetros Clave

#### `model`

Modelos recomendados:

| Modelo | RAM Necesaria | Velocidad | Calidad | Uso Recomendado |
|--------|---------------|-----------|---------|-----------------|
| `llama3.2:3b` | 4GB | Rápido | Buena | Uso general (recomendado) |
| `phi3:mini` | 2GB | Muy rápido | Aceptable | Hardware limitado |
| `mistral:7b` | 8GB | Lento | Excelente | Máxima calidad |

**Cambiar modelo:**
```bash
# Descargar modelo
ollama pull mistral:7b

# Editar config/ollama_config.yaml
model: "mistral:7b"
```

#### `temperature`

Controla aleatoriedad de la salida:

- **0.1** - Muy determinista, respuestas idénticas (recomendado para producción)
- **0.2** - Balance (default)
- **0.3-0.5** - Más variabilidad, útil para experimentación

**Síntoma:** JSON inválido frecuente → **Bajar temperatura a 0.1**

#### `max_tokens`

Longitud máxima de respuesta:

- **2000** - Documentos cortos (1-3 páginas)
- **4000** - Documentos medios (5-10 páginas) - **Default**
- **8000** - Documentos largos (chunking automático se activa)

---

## 🔄 Reintentos Automáticos

Ubicación: **`src/orchestration/analyzer.py`**

```python
MAX_RETRIES = 2  # Número de reintentos si JSON inválido
```

Si el LLM devuelve JSON inválido:

1. **Primer intento:** Envía prompt original
2. **Segundo intento:** Envía prompt con corrección: _"Tu respuesta anterior no era JSON válido. Devuelve SOLO JSON con el esquema..."_
3. **Tercer intento:** Último intento con mayor énfasis

Si tras 3 intentos falla → Excepción `ValidationError`

---

## 📊 Ejemplos de Personalización

### Ejemplo 1: Documentos Médicos

```python
# prompts.py
LLM_SPECIFY = """
{
  // ... campos existentes ...
  "diagnosticos": ["string"],
  "medicamentos": [{"nombre": "string", "dosis": "string"}],
  "alergias": ["string"]
}
"""

LLM_PLAN = """
// ... pasos existentes ...
10. Extraer DIAGNÓSTICOS del informe médico
11. Listar MEDICAMENTOS con dosis prescritas
12. Identificar ALERGIAS o contraindicaciones
"""
```

### Ejemplo 2: Contratos en Inglés

```python
# prompts.py
LLM_CONSTITUTION = """
1. Extract information ONLY from the document text.
2. Return answers in ENGLISH.
3. Use ISO date format: YYYY-MM-DD.
"""
```

```yaml
# config/ollama_config.yaml
model: "llama3.2:3b"
language: "en"  # Añadir campo personalizado
```

### Ejemplo 3: Resumen Más Largo

```python
# prompts.py
LLM_SPECIFY = """
"resumen_bullets": ["string"],  # 10-15 bullets (aumentado desde 5-10)
"""

LLM_PLAN = """
7. Generar RESUMEN (10–15 bullets, máximo detalle).
"""
```

---

## 🧪 Testing de Prompts

Para probar cambios en prompts:

1. **Edita** `src/orchestration/prompts.py`
2. **Reinicia** la aplicación: `streamlit run src/ui/app.py`
3. **Analiza** documento de prueba
4. **Revisa** salida en pantalla y JSON exportado

**Script de prueba directa:**
```bash
python -c "from src.orchestration.ollama_client import OllamaClient; client = OllamaClient(); print(client.generate('Tu prompt aquí'))"
```

---

## ⚠️ Advertencias

1. **No eliminar campos requeridos** del esquema JSON - romperá validación Pydantic
2. **Temperatura > 0.5** puede causar JSON inválido frecuente
3. **Prompts muy largos** (> 2000 palabras) aumentan latencia sin mejorar resultados
4. **Reiniciar aplicación** tras cambios en prompts (no se recargan dinámicamente)

---

## 📚 Recursos Adicionales

- **Ollama Model Library:** https://ollama.ai/library
- **Prompt Engineering Guide:** https://www.promptingguide.ai/
- **Pydantic Docs:** https://docs.pydantic.dev/

---

**¿Necesitas ayuda?** Consulta `docs/troubleshooting.md` si los cambios no funcionan como esperas.
