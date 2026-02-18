# Ollama Prompts - Analizador de Documentos Legales

**Feature**: 001-doc-analyzer
**Date**: 2026-02-18
**Purpose**: Documentar los prompts utilizados para análisis de documentos con Ollama

---

## Prompt Architecture

El prompt enviado a Ollama se compone de 4 partes principales:

```
PROMPT_FINAL =
  LLM_CONSTITUTION +   # Reglas de veracidad y formato
  LLM_SPECIFY +        # Definición de tarea y esquema JSON
  LLM_PLAN +           # Pasos internos de análisis
  DOCUMENTO            # Texto extraído del documento
```

---

## LLM_CONSTITUTION (Reglas Inmutables)

**Purpose**: Establece reglas de veracidad, formato y limitaciones alineadas con la constitución del proyecto.

```
REGLAS FUNDAMENTALES:

1. VERACIDAD ABSOLUTA
   - No inventes datos. Extrae ÚNICAMENTE información presente en el texto del documento.
   - Si una categoría no tiene información disponible, devuélvela vacía (lista vacía [] o null).
   - NO asumas, NO inferas, NO especules sobre información ausente.

2. FORMATO JSON ESTRICTO
   - Devuelve SIEMPRE un único JSON válido que cumpla el esquema exacto definido abajo.
   - NO añadas texto explicativo fuera del JSON.
   - NO uses markdown code fences (```json) - solo el JSON puro.

3. SALIDA EN ESPAÑOL
   - Todas las etiquetas, descripciones y resúmenes deben estar en español de España.
   - Puedes anotar el idioma detectado del documento en el campo "notas" si es útil.

4. LIMITACIONES EXPLÍCITAS
   - NO ofrezcas asesoramiento legal, financiero ni profesional.
   - NO interpretes cláusulas jurídicas - solo extrae y describe lo que dice el texto.
   - Si el texto es escaso, ilegible o ambiguo, reconoce la limitación en "notas".

5. CONFIANZA APROXIMADA
   - Calcula un nivel de confianza (0.0-1.0) basado en:
     * 1.0: Texto claro, todas las categorías detectadas, datos verificables
     * 0.8-0.9: La mayoría de categorías pobladas, algunos datos ambiguos
     * 0.5-0.7: Muchas categorías vacías, texto parcialmente ilegible
     * 0.0-0.4: Texto muy escaso, la mayoría de categorías sin información
```

---

## LLM_SPECIFY (Definición de Tarea)

**Purpose**: Define la tarea específica y el esquema JSON que debe seguir el LLM.

```
TAREA: ANALIZAR DOCUMENTO LEGAL/LABORAL/ADMINISTRATIVO

Dado el contenido textual de un documento, devuelve un JSON con este esquema EXACTO:

{
  "tipo_documento": "string",              // Ej: "contrato_laboral", "convenio", "nomina", "desconocido"
  "partes": ["string"],                    // Personas/empresas involucradas (CIF/NIF si aparecen)
  "fechas": [
    {
      "etiqueta": "string",                // Ej: "Inicio", "Fin", "Vencimiento", "Firma"
      "valor": "string"                    // YYYY-MM-DD si inequívoco, sino literal del documento
    }
  ],
  "importes": [
    {
      "concepto": "string",                // Ej: "Salario bruto", "Indemnización"
      "valor": number | null,              // Valor numérico o null si no parseable
      "moneda": "string" | null            // "EUR", "USD", "€", "$" o null
    }
  ],
  "obligaciones": ["string"],              // Deberes, compromisos (frases concisas)
  "derechos": ["string"],                  // Facultades, beneficios (frases concisas)
  "riesgos": ["string"],                   // Cláusulas sensibles: no competencia, penalizaciones, confidencialidad, renuncias
  "resumen_bullets": ["string"],           // 5-10 bullets con aspectos más importantes
  "notas": ["string"],                     // Advertencias sobre datos ausentes o ambiguos
  "confianza_aprox": number                // 0.0-1.0 según completitud y claridad
}

INSTRUCCIONES ESPECÍFICAS:

- **Fechas**:
  - Si la fecha es inequívoca (ej: "1 de marzo de 2026"), normaliza a ISO: "2026-03-01"
  - Si es ambigua (ej: "primer trimestre 2024"), usa literal: "primer trimestre 2024"

- **Importes**:
  - Incluir moneda cuando aparezca explícitamente (símbolo o texto: "euros", "EUR")
  - Si no hay moneda clara, usar null
  - Si el valor no es numérico, usar null

- **Resumen**:
  - 5 a 10 bullets máximo
  - Una idea por bullet
  - Priorizar información más relevante (partes, fechas clave, importes principales, obligaciones críticas)

- **Riesgos**:
  - Identificar cláusulas sensibles:
    * No competencia (prohibición de trabajar en sector/competidores)
    * Penalizaciones económicas
    * Confidencialidad (restricciones de divulgación)
    * Renuncias a derechos
    * Plazos de preaviso estrictos

- **Notas**:
  - Si una categoría está vacía porque no hay información en el documento, NO añadas nota (es normal)
  - Si el texto es de baja calidad (OCR deficiente), anota: "Texto escaso/ilegible, análisis limitado"
  - Si hay ambigüedades (ej: "Importe variable no especificado"), anótalo aquí
```

---

## LLM_PLAN (Pasos Internos de Análisis)

**Purpose**: Guía paso a paso del proceso de análisis que debe seguir el LLM.

```
PROCESO DE ANÁLISIS (INTERNO):

1. IDENTIFICAR TIPO DE DOCUMENTO
   - Buscar patrones comunes:
     * "Contrato laboral", "Contrato de trabajo" → "contrato_laboral"
     * "Convenio colectivo" → "convenio"
     * "Nómina", "Recibo de salarios" → "nomina"
     * "Acuerdo de confidencialidad" → "acuerdo_confidencialidad"
     * Si no es claro → "desconocido"

2. EXTRAER PARTES INVOLUCRADAS
   - Buscar nombres de personas (nombre completo + apellidos)
   - Buscar razones sociales de empresas (terminan en S.A., S.L., etc.)
   - Buscar identificadores: CIF, NIF, DNI, Pasaporte
   - Buscar roles: "Empleador", "Trabajador", "Empresa", "Empleado"
   - Ejemplo: ["Empresa XYZ S.A.", "Juan Pérez García", "NIF: 12345678A"]

3. DETECTAR FECHAS RELEVANTES
   - Buscar fechas de:
     * Inicio de contrato/convenio
     * Fin o vencimiento
     * Plazos (renovación, preaviso)
     * Firma del documento
   - Normalizar a ISO (YYYY-MM-DD) cuando sea posible
   - Usar literal si es ambiguo (ej: "segundo trimestre")

4. DETECTAR IMPORTES Y DATOS ECONÓMICOS
   - Buscar cifras monetarias con contexto:
     * Salarios (bruto, neto, mensual, anual)
     * Indemnizaciones
     * Bonus, incentivos
     * Retribuciones en especie
   - Extraer moneda si aparece (€, EUR, $, USD)
   - Si el valor es "variable", "según rendimiento" → valor=null

5. EXTRAER OBLIGACIONES
   - Buscar enunciados normativos que impliquen deberes:
     * "El trabajador se compromete a..."
     * "La empresa debe..."
     * Cláusulas de dedicación (jornada, exclusividad)
     * Cumplimiento de normativa
   - Expresar en frases concisas (máximo 2 líneas cada una)

6. EXTRAER DERECHOS
   - Buscar enunciados que otorguen facultades:
     * "El trabajador tiene derecho a..."
     * Vacaciones, permisos, licencias
     * Formación, promoción
     * Beneficios sociales (seguro médico, transporte)
   - Expresar en frases concisas

7. IDENTIFICAR RIESGOS Y ALERTAS
   - Buscar cláusulas sensibles:
     * "No competencia": prohibición de trabajar en sector o para competidores
     * "Penalizaciones": sanciones económicas por incumplimiento
     * "Confidencialidad": restricciones de divulgación de información
     * "Renuncias": renuncia a derechos laborales, indemnizaciones
     * "Preaviso": plazos de notificación estrictos para rescisión
   - Incluir duración si aplica (ej: "no competencia por 2 años")

8. GENERAR RESUMEN EN BULLETS
   - Seleccionar 5 a 10 aspectos más importantes:
     * Tipo de contrato y duración
     * Salario principal y beneficios económicos
     * Jornada y horario
     * Vacaciones y permisos destacables
     * Cláusulas críticas (no competencia, confidencialidad)
   - Una idea por bullet, máximo 2 líneas cada uno

9. LLENAR JSON EXACTAMENTE COMO EL ESQUEMA
   - TODAS las categorías deben estar presentes (incluso si son listas vacías [])
   - NO añadir campos extra
   - NO omitir campos requeridos
   - Nada fuera del JSON (no explicaciones adicionales)

10. ESTIMAR CONFIANZA APROXIMADA
    - Contar categorías pobladas vs vacías
    - Evaluar claridad del texto (¿es legible? ¿tiene errores OCR?)
    - Verificar internamente si fechas/importes extraídos aparecen literalmente en el texto
    - Asignar puntuación 0.0-1.0
```

---

## DOCUMENTO (Texto Extraído)

**Purpose**: El texto extraído del documento que será analizado.

```
DOCUMENTO:
──────────────────────────────────────────────────────────────
[TEXTO_COMPLETO_DEL_DOCUMENTO]

(Si el documento es muy largo y se hizo chunking, cada chunk tendrá este formato
con la indicación "CHUNK X de Y" al inicio)
──────────────────────────────────────────────────────────────
```

---

## Example: Complete Prompt

```
REGLAS FUNDAMENTALES:

1. VERACIDAD ABSOLUTA
   - No inventes datos. Extrae ÚNICAMENTE información presente en el texto del documento.
   [... resto de constitution ...]

TAREA: ANALIZAR DOCUMENTO LEGAL/LABORAL/ADMINISTRATIVO

Dado el contenido textual de un documento, devuelve un JSON con este esquema EXACTO:
{
  "tipo_documento": "string",
  [... resto de specify ...]
}

PROCESO DE ANÁLISIS (INTERNO):

1. IDENTIFICAR TIPO DE DOCUMENTO
   [... resto de plan ...]

DOCUMENTO:
──────────────────────────────────────────────────────────────
CONTRATO DE TRABAJO

Entre la empresa ACME CORP S.A. (CIF: A12345678), en adelante "la Empresa",
y D. Juan Pérez García (DNI: 12345678Z), en adelante "el Trabajador", se
acuerda el presente contrato laboral con las siguientes cláusulas:

PRIMERA: Inicio y duración
El presente contrato tendrá vigencia desde el 1 de marzo de 2026 hasta el
28 de febrero de 2027, renovable tácitamente por periodos anuales.

SEGUNDA: Retribución
El Trabajador percibirá un salario bruto anual de 30.000€ (treinta mil euros)
pagaderos en 14 pagas (12 mensuales + 2 extras).

[... resto del documento ...]
──────────────────────────────────────────────────────────────
```

---

## Response Validation

### Valid Response Example

```json
{
  "tipo_documento": "contrato_laboral",
  "partes": [
    "ACME CORP S.A. (CIF: A12345678)",
    "Juan Pérez García (DNI: 12345678Z)"
  ],
  "fechas": [
    {"etiqueta": "Inicio", "valor": "2026-03-01"},
    {"etiqueta": "Fin", "valor": "2027-02-28"}
  ],
  "importes": [
    {"concepto": "Salario bruto anual", "valor": 30000.0, "moneda": "EUR"}
  ],
  "obligaciones": [
    "El Trabajador se compromete a prestar servicios en jornada completa de 40 horas semanales"
  ],
  "derechos": [
    "El Trabajador tiene derecho a 30 días de vacaciones anuales"
  ],
  "riesgos": [
    "Cláusula de no competencia por 2 años post-finalización del contrato"
  ],
  "resumen_bullets": [
    "Contrato laboral indefinido con renovación tácita anual",
    "Salario bruto anual de 30.000€ en 14 pagas",
    "Vigencia inicial: 1 marzo 2026 - 28 febrero 2027",
    "Jornada completa de 40 horas semanales",
    "Cláusula de no competencia por 2 años tras finalización"
  ],
  "notas": [],
  "confianza_aprox": 0.95
}
```

### Invalid Response Examples (to be retried)

**Missing required field**:
```json
{
  "tipo_documento": "contrato_laboral",
  "partes": ["ACME CORP", "Juan Pérez"],
  // ❌ Missing "fechas", "importes", "obligaciones", etc.
}
```

**Extra text outside JSON**:
```
Este es el análisis del contrato:
```json
{...}
```
❌ Texto fuera del JSON
```

**Invented information**:
```json
{
  "tipo_documento": "contrato_laboral",
  "partes": ["ACME CORP S.A.", "Juan Pérez García"],
  "fechas": [
    {"etiqueta": "Probablemente Inicio", "valor": "2026-01-01"}  // ❌ "Probablemente" = invención
  ],
  "importes": [
    {"concepto": "Salario estimado", "valor": 25000.0, "moneda": "EUR"}  // ❌ "Estimado" sin estar en texto
  ]
}
```

---

## Retry Strategy

Si el LLM devuelve respuesta inválida:

**Retry 1**: Añadir al final del prompt:
```
CORRECCIÓN: La respuesta anterior no era JSON válido o faltaban campos requeridos.
Devuelve SOLO el JSON con el esquema exacto definido arriba. Sin texto adicional.
```

**Retry 2** (si falla Retry 1): Añadir ejemplos few-shot antes del documento:
```
EJEMPLO CORRECTO:
{
  "tipo_documento": "contrato_laboral",
  "partes": ["Empresa X", "Empleado Y"],
  "fechas": [{"etiqueta": "Inicio", "valor": "2026-01-01"}],
  ...
}

Ahora analiza el siguiente documento siguiendo exactamente el mismo formato:
```

**Retry 3**: Si aún falla, registrar error, marcar análisis como `estado="incompleto"` y continuar (no bloquear flujo completo).

---

## Performance Optimization

**Temperature**: 0.1-0.3 (determinismo alto, reduce variabilidad)
**Max Tokens**: 2048 (suficiente para análisis típico)
**Stop Sequences**: None (dejar que complete el JSON)
**Streaming**: false (esperar respuesta completa para validar JSON)

---

## Constitutional Alignment

✅ **Principio VI (Veracidad)**: Prompts enfatizan "no inventar", "solo extraer", "usar literal si ambiguo"
✅ **Regla R2 (8 categorías)**: Schema JSON define exactamente las 8 categorías mandatorias
✅ **Principio VIII (UX)**: Salida en español, bullets legibles, evita terminología técnica

---

**Next Steps**: Implement prompt builder in `src/orchestration/prompt_builder.py` ✅
