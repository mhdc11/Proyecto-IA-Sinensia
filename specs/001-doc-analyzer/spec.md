# Feature Specification: Analizador de Documentos Legales

**Feature Branch**: `001-doc-analyzer`
**Created**: 2026-02-18
**Status**: Draft
**Input**: User description: "Sistema para analizar documentos legales, laborales y administrativos, extrayendo puntos clave y presentándolos de forma clara con historial navegable de duplas (documento ↔ análisis)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Análisis Individual de Documento (Priority: P1)

El usuario carga un único documento (PDF, DOCX o imagen escaneada), el sistema extrae el texto y genera automáticamente un análisis estructurado en 8 categorías clave: partes involucradas, fechas relevantes, importes, obligaciones, derechos, riesgos/alertas, resumen en bullets y tipo de documento. Los resultados se presentan visualmente con secciones diferenciadas para cada categoría.

**Why this priority**: Este es el MVP mínimo viable que entrega valor inmediato. Un usuario puede cargar un documento y obtener un análisis estructurado en segundos, reduciendo el tiempo de revisión manual de horas a minutos. Es la funcionalidad core que habilita todos los demás casos de uso.

**Independent Test**: Puede ser completamente testeado cargando un único documento y verificando que se genera y muestra el análisis con las 8 categorías. Entrega valor standalone sin depender de otras historias.

**Acceptance Scenarios**:

1. **Given** el usuario abre la aplicación sin documentos previos, **When** carga un PDF nativo con texto embebido (ej: contrato laboral), **Then** el sistema extrae el texto, genera el análisis y muestra las 8 categorías con contenido en aquellas que apliquen y "No disponible" en las que no
2. **Given** el usuario carga un documento, **When** una o más categorías no tienen información extraíble, **Then** el sistema indica explícitamente "No disponible" o "No aplica" sin inventar información
3. **Given** el usuario carga un PDF escaneado (imagen), **When** el sistema procesa el documento, **Then** extrae texto mediante OCR, genera análisis con al menos resumen en bullets y categorías detectables, y muestra advertencia si la calidad es baja sin detener el flujo
4. **Given** el usuario carga un documento DOCX, **When** el sistema procesa el archivo, **Then** extrae texto nativamente y genera análisis con la misma estructura de 8 categorías
5. **Given** el usuario carga un documento, **When** el análisis está en proceso, **Then** se muestra indicador de progreso con estados claros ("Extrayendo texto...", "Analizando contenido...", "Generando resumen...")
6. **Given** el usuario carga un archivo corrupto o ilegible, **When** el sistema intenta procesarlo, **Then** muestra mensaje de error comprensible ("No se pudo leer el archivo. Verifica que no esté dañado.") sin bloquear la aplicación

---

### User Story 2 - Historial de Duplas (Priority: P2)

El sistema mantiene un historial persistente de todas las duplas (documento ↔ análisis) realizadas, presentado en una lista lateral similar a un historial de chat. El usuario puede seleccionar cualquier entrada para recuperar y visualizar su análisis asociado, o eliminar entradas para mantener el historial relevante.

**Why this priority**: Añade valor significativo al permitir consultas recurrentes y comparaciones entre documentos. Los documentos legales suelen requerir múltiples revisiones y referencias cruzadas. El historial transforma la herramienta de un analizador único en una biblioteca de análisis reutilizable.

**Independent Test**: Después de implementar US1, se puede verificar que cada análisis generado se persiste, aparece en el historial lateral, puede ser seleccionado para recuperar su análisis, y puede ser eliminado sin afectar otros registros.

**Acceptance Scenarios**:

1. **Given** el usuario completa el análisis de un documento (US1), **When** revisa el historial lateral, **Then** aparece una nueva entrada con el nombre del archivo, tipo de documento (si fue determinado) y fecha/hora de análisis
2. **Given** el historial contiene 3 análisis previos, **When** el usuario selecciona la segunda entrada, **Then** se muestra el análisis asociado a ese documento específico sin alterar el historial
3. **Given** el usuario selecciona una entrada del historial con múltiples categorías vacías, **When** visualiza el análisis, **Then** mantiene la misma estructura visual indicando "No disponible" donde corresponda
4. **Given** el usuario selecciona una entrada del historial, **When** hace clic en "Eliminar", **Then** el sistema solicita confirmación ("¿Eliminar este análisis del historial? Esta acción no se puede deshacer"), y tras aceptar, la entrada desaparece sin afectar otras
5. **Given** el usuario cierra y reabre la aplicación, **When** revisa el historial, **Then** todas las duplas previas siguen accesibles (persistencia local)
6. **Given** el historial contiene 10+ entradas, **When** el usuario navega por la lista, **Then** puede desplazarse fácilmente con scroll y distinguir cada entrada por su título y metadatos

---

### User Story 3 - Carga y Análisis Múltiple (Priority: P2)

El usuario puede cargar varios documentos simultáneamente en una misma sesión, el sistema procesa cada uno de forma individual y mantiene la misma estructura visual de análisis para todos, facilitando la comparación directa entre documentos.

**Why this priority**: Casos de uso comunes involucran revisar múltiples contratos, nóminas o anexos de forma conjunta. El análisis batch acelera flujos de trabajo de revisión masiva (ej: analista de compliance revisando 20 contratos) y mantiene consistencia visual para comparación eficiente.

**Independent Test**: Extensión de US1 verificable cargando 3+ documentos juntos y confirmando que cada uno genera su análisis independiente con estructura consistente y todos aparecen en el historial.

**Acceptance Scenarios**:

1. **Given** el usuario selecciona opción de carga múltiple, **When** elige 5 documentos de diferentes formatos (3 PDF, 1 DOCX, 1 imagen), **Then** el sistema procesa todos y genera 5 análisis independientes
2. **Given** el usuario carga 3 documentos simultáneamente, **When** revisa cada análisis, **Then** todos mantienen el mismo orden de categorías (partes, fechas, importes, obligaciones, derechos, riesgos, resumen, tipo) facilitando comparación visual
3. **Given** el usuario carga múltiples documentos con calidad variable, **When** uno falla (archivo corrupto), **Then** el sistema muestra error para ese archivo específico pero continúa procesando los demás sin interrumpir el batch
4. **Given** el usuario carga 10 documentos, **When** el procesamiento está en curso, **Then** se muestra progreso global ("Procesando 3 de 10...") y puede cancelar la operación si necesario
5. **Given** el usuario completa carga múltiple de 7 documentos, **When** revisa el historial lateral, **Then** aparecen 7 nuevas entradas ordenadas cronológicamente con metadatos claros

---

### User Story 4 - Exportación de Resultados (Priority: P3)

El usuario puede exportar el análisis de un documento en un formato estructurado y legible (JSON) que preserva todas las categorías y su contenido, permitiendo uso externo del análisis sin alterar la experiencia de visualización en pantalla.

**Why this priority**: Habilita integración con otros sistemas (ej: importar a hojas de cálculo, bases de datos, herramientas de BI) y respaldo de análisis. Es valiosa para workflows avanzados pero no crítica para el flujo básico de revisión.

**Independent Test**: Funcionalidad aislada verificable exportando un análisis completo, abriendo el archivo generado y confirmando que contiene todas las categorías con formato estructurado legible.

**Acceptance Scenarios**:

1. **Given** el usuario visualiza el análisis de un documento, **When** hace clic en "Exportar", **Then** se genera un archivo JSON con estructura `{"documento": {...}, "analisis": {"partes": [...], "fechas": [...], ...}, "metadata": {...}}`
2. **Given** el usuario exporta un análisis con múltiples categorías vacías, **When** abre el archivo exportado, **Then** las categorías vacías aparecen como arrays/listas vacías `"obligaciones": []` manteniendo la estructura
3. **Given** el usuario selecciona múltiples análisis del historial, **When** elige "Exportar selección", **Then** genera un único archivo JSON con array de análisis `{"analisis": [{doc1}, {doc2}, ...]}`
4. **Given** el usuario exporta un análisis, **When** el archivo se genera, **Then** el nombre del archivo incluye el nombre del documento original y timestamp (ej: `contrato-laboral-2026-02-18-143022.json`)
5. **Given** el usuario exporta un análisis, **When** revisa el JSON generado, **Then** todos los caracteres especiales (ñ, acentos, símbolos monetarios) se preservan correctamente en UTF-8

---

### Edge Cases

- **¿Qué pasa cuando el usuario carga un documento de 500+ páginas?** El sistema muestra advertencia de procesamiento largo, permite cancelar, y mantiene indicador de progreso con tiempo estimado.
- **¿Cómo maneja el sistema documentos con tablas complejas o gráficos?** Extrae texto legible de tablas preservando estructura básica, ignora gráficos/imágenes decorativos, y advierte si el contenido visual crítico no pudo extraerse.
- **¿Qué pasa si el usuario carga un documento en inglés pero la app está en español?** El análisis detecta el idioma del documento (metadata), extrae en idioma original, y presenta categorías/labels en español con contenido en inglés (ej: "Partes involucradas: [company name in English]").
- **¿Cómo responde el sistema a documentos con formatos híbridos (PDF con imágenes embebidas + texto nativo)?** Procesa ambas partes: extrae texto nativo directamente, aplica OCR a imágenes embebidas, y combina resultados en un único análisis.
- **¿Qué sucede si el usuario intenta cargar un archivo de 2GB?** El sistema valida tamaño máximo razonable (ej: 100MB), rechaza archivos excesivamente grandes con mensaje claro ("Archivo demasiado grande. Máximo: 100MB"), y sugiere dividir el documento.
- **¿Cómo maneja el sistema duplicados en el historial?** Si el usuario carga el mismo archivo dos veces, genera dos análisis separados con timestamps distintos (R1: cada ejecución = nueva dupla), permitiendo ver evolución si el documento fue modificado.
- **¿Qué pasa si el almacenamiento local se llena?** El sistema detecta espacio insuficiente, advierte al usuario antes de fallar, y sugiere eliminar entradas antiguas del historial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEBE permitir al usuario cargar uno o múltiples documentos en formatos PDF (nativo y escaneado), DOCX e imágenes (PNG, JPG) en una misma sesión
- **FR-002**: Sistema DEBE extraer texto de documentos nativos (PDF con texto embebido, DOCX) directamente sin pérdida de contenido
- **FR-003**: Sistema DEBE aplicar reconocimiento óptico de caracteres (OCR) a documentos escaneados e imágenes para convertirlos en texto analizable
- **FR-004**: Sistema DEBE generar para cada documento un análisis estructurado en exactamente 8 categorías: Partes involucradas, Fechas relevantes, Importes/datos económicos, Obligaciones, Derechos, Riesgos/alertas, Resumen en bullets, y Tipo de documento
- **FR-005**: Sistema DEBE presentar el análisis con secciones visuales diferenciadas para cada categoría, usando listas/bullets para escaneabilidad rápida
- **FR-006**: Sistema DEBE indicar explícitamente "No disponible" o "No aplica" cuando una categoría no contenga información extraíble, sin inventar contenido
- **FR-007**: Sistema DEBE mantener orden consistente de categorías entre todos los documentos independientemente del formato original o contenido
- **FR-008**: Sistema DEBE persistir cada dupla (documento ↔ análisis) en almacenamiento local después de completar el análisis
- **FR-009**: Sistema DEBE presentar historial de duplas en una lista lateral tipo conversación, mostrando nombre de archivo, tipo de documento (si determinado) y timestamp de análisis
- **FR-010**: Sistema DEBE permitir al usuario seleccionar cualquier entrada del historial para recuperar y visualizar su análisis asociado
- **FR-011**: Sistema DEBE permitir al usuario eliminar entradas individuales del historial con confirmación previa ("¿Eliminar este análisis?"), sin afectar otras duplas
- **FR-012**: Sistema DEBE permitir reordenar entradas del historial (cronológico descendente por defecto, opción de ascendente o alfabético)
- **FR-013**: Sistema DEBE exportar análisis en formato JSON estructurado preservando todas las categorías y contenido con codificación UTF-8
- **FR-014**: Sistema DEBE detectar idioma del documento y registrarlo en metadata, presentando labels de categorías en español y contenido en idioma original
- **FR-015**: Sistema DEBE mostrar indicadores de progreso durante extracción de texto y análisis con estados descriptivos ("Extrayendo texto...", "Analizando contenido...", "Generando resumen...")
- **FR-016**: Sistema DEBE manejar errores de carga (archivo corrupto, formato no soportado, archivo demasiado grande) con mensajes claros sin bloquear la aplicación
- **FR-017**: Sistema DEBE permitir al usuario cancelar operaciones de procesamiento en curso (carga, extracción, análisis)
- **FR-018**: Sistema DEBE validar tamaño máximo de archivo (100MB) y rechazar archivos excesivos con mensaje explicativo
- **FR-019**: Sistema DEBE procesar documentos de baja calidad (escaneos deficientes) de forma tolerante, generando análisis parcial y mostrando advertencia sin fallar
- **FR-020**: Sistema DEBE preservar caracteres especiales (ñ, acentos, símbolos monetarios €$£) en extracción, análisis y exportación

### Key Entities

- **Documento**: Representa el archivo cargado por el usuario. Atributos: identificador único (UUID), nombre de archivo original, tipo MIME, tamaño en bytes, formato detectado (PDF_NATIVO, PDF_ESCANEADO, DOCX, IMAGEN), número de páginas, idioma detectado, hash SHA-256 del contenido (para detectar duplicados), ruta de almacenamiento temporal del archivo original.

- **TextoExtraído**: Contenido textual obtenido del documento. Atributos: referencia al documento origen, método de extracción utilizado (NATIVO, OCR, HÍBRIDO), texto completo, calidad de extracción (ALTA, MEDIA, BAJA), advertencias generadas durante extracción, timestamp de extracción.

- **Análisis**: Resultado estructurado del procesamiento del documento. Atributos: referencia al documento origen, **partes** (lista de entidades/denominaciones identificadas), **fechas** (lista de tuplas `{etiqueta, valor, formato}`), **importes** (lista de tuplas `{concepto, valor, moneda}`), **obligaciones** (lista de enunciados textuales), **derechos** (lista de enunciados textuales), **riesgos** (lista de cláusulas/alertas identificadas), **resumen** (lista de 3-7 bullets con aspectos clave), **tipoDocumento** (etiqueta categórica: CONTRATO_LABORAL, NÓMINA, CONVENIO, PODER_NOTARIAL, ACUERDO_CONFIDENCIALIDAD, OTRO, INDETERMINADO), observaciones adicionales (notas sobre campos no disponibles o advertencias), timestamp de análisis, versión del modelo de análisis utilizado.

- **Dupla**: Asociación persistente entre un documento y su análisis. Atributos: identificador único, referencia al documento, referencia al análisis, fecha/hora de creación, fecha/hora de última visualización, estado (COMPLETO, PARCIAL, CON_ADVERTENCIAS, ERROR), flag de favorito (para funcionalidad futura), etiquetas personalizadas (para funcionalidad futura).

- **HistorialEntry**: Representación visual de una dupla en el historial lateral. Atributos: referencia a la dupla, título de visualización (nombre del documento), subtítulo (tipo de documento), icono representativo, timestamp de creación, indicador de estado visual (color/badge).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuarios completan la revisión de un documento legal en menos de 5 minutos (reducción del 70% respecto a revisión manual que toma 15-20 minutos)
- **SC-002**: El sistema procesa exitosamente al menos 95% de documentos PDF nativos sin errores de extracción
- **SC-003**: El sistema identifica y extrae al menos 4 de las 8 categorías en el 85% de documentos legales estándar (contratos, nóminas, convenios)
- **SC-004**: Usuarios pueden comprender los puntos clave de un documento sin leer el contenido completo en el 90% de casos (validado por test de comprensión)
- **SC-005**: El sistema genera análisis completo de un documento de 10-20 páginas en menos de 30 segundos en hardware estándar
- **SC-006**: Usuarios recuperan y visualizan análisis previos del historial en menos de 3 segundos
- **SC-007**: El sistema procesa documentos escaneados de calidad media/baja con al menos 80% de precisión en extracción de texto (medido por comparación con transcripción manual)
- **SC-008**: Cero invención de información: 100% del contenido del análisis debe ser verificable contra el documento fuente (auditoría manual de 50 análisis aleatorios)
- **SC-009**: Tasa de error catastrófico (falla completa de la aplicación) inferior al 1% de documentos procesados
- **SC-010**: Usuarios exportan análisis en formato JSON sin pérdida de información en el 100% de casos
- **SC-011**: Sistema mantiene consistencia visual (mismo orden de categorías, mismos labels) en el 100% de análisis generados
- **SC-012**: Satisfacción del usuario: al menos 80% de usuarios reportan que el sistema "acelera significativamente" su trabajo de revisión documental (encuesta post-uso)

## Assumptions & Constraints *(optional)*

### Assumptions

- Los documentos cargados por el usuario son legítimos y están autorizados para su lectura y análisis
- Los usuarios tienen conocimientos básicos de ofimática (abrir archivos, navegar carpetas)
- Los documentos son principalmente en español, con soporte secundario para inglés y otros idiomas europeos
- La mayoría de documentos tendrán entre 1-50 páginas (98% de casos de uso)
- Los usuarios aceptan que el análisis es apoyo a la lectura, no un dictamen legal vinculante
- El entorno de ejecución tiene al menos 4GB RAM y procesador dual-core moderno (últimos 5 años)
- El almacenamiento local tiene al menos 2GB disponibles para historial y caché

### Constraints

- **Privacidad mandatoria**: Procesamiento 100% local, sin transmisión de documentos o análisis a servicios externos sin consentimiento explícito (Principio I - Constitución)
- **Veracidad absoluta**: Prohibida la invención o inferencia especulativa de información no respaldada por el documento (Principio VI - Constitución)
- **Estructura inmutable**: Las 8 categorías y su orden no pueden alterarse entre documentos (Regla R5 - Constitución)
- **Sin asesoramiento**: El sistema no puede ofrecer interpretaciones legales, recomendaciones o predicciones (Limitaciones Deliberadas - Constitución)
- **Independencia de formato**: El análisis debe ser idéntico independientemente del formato original (PDF vs DOCX del mismo contenido)
- **Límite de tamaño**: Documentos máximos de 100MB (restricción práctica de rendimiento)
- **Context window del LLM**: ~4000 tokens (llama3.2:3b) requiere chunking para documentos >10 páginas, con consolidación posterior para mantener análisis coherente (ver T023 en tasks.md)
- **Idioma de salida**: Por defecto español, configurable a otros idiomas en versiones futuras

## Out of Scope *(optional)*

- **Edición de documentos**: El sistema solo lee y analiza, nunca modifica el documento original
- **Asesoramiento legal**: No genera recomendaciones, opiniones jurídicas ni conclusiones profesionales
- **Interpretación predictiva**: No predice resultados de litigios, riesgos futuros no explícitos, o consecuencias legales
- **Validación formal**: No sustituye auditorías legales, compliance reviews profesionales o validación notarial
- **Análisis comparativo automático**: No compara múltiples documentos para identificar diferencias (funcionalidad futura potencial)
- **Generación de documentos**: No crea contratos, cláusulas o documentos legales basados en plantillas
- **Integración con sistemas externos**: No se conecta a bases de datos jurídicas, APIs de terceros o servicios cloud en versión MVP
- **Firma digital o gestión documental**: No maneja workflow de aprobaciones, firmas electrónicas o versionado de documentos
- **Traducción automática**: No traduce documentos completos, solo detecta idioma y presenta análisis en idioma del usuario
- **Análisis de imágenes/gráficos**: No interpreta diagramas, organigramas, fotos o contenido visual más allá de extracción OCR de texto

## Dependencies *(optional)*

### External Dependencies

- **Biblioteca de extracción PDF**: Capacidad de parsear PDF nativos y extraer texto estructurado preservando layout básico
- **Motor OCR**: Tecnología de reconocimiento óptico de caracteres para documentos escaneados e imágenes (calidad crítica para Success Criteria SC-007)
- **Modelo de análisis de lenguaje natural**: Capacidad de identificar entidades (partes, fechas, importes), clasificar enunciados (obligaciones vs derechos), detectar cláusulas sensibles (riesgos), y generar resúmenes
- **Almacenamiento local persistente**: Sistema de archivos o base de datos local para historial de duplas

### Risk Mitigation

- **Riesgo de calidad OCR**: Documentos extremadamente deteriorados pueden limitar valor del análisis → Mitigación: Advertencias claras, análisis parcial viable, sugerencia de mejorar calidad de escaneo
- **Riesgo de expectativas excesivas**: Usuarios esperan interpretación legal → Mitigación: Disclaimers visibles, educación en onboarding, límites claros en UI
- **Riesgo de privacidad percibida**: Usuarios temen fuga de documentos sensibles → Mitigación: Badge "100% Local" visible, no requerir conexión internet, documentación de arquitectura privacy-first
- **Riesgo de formatos heterogéneos**: PDFs con layouts complejos (columnas múltiples, tablas anidadas) pueden degradar extracción → Mitigación: Detección de complejidad, advertencias, extracción best-effort
- **Riesgo de rendimiento**: Documentos de 100+ páginas pueden ser lentos → Mitigación: Límite de tamaño, procesamiento asíncrono con cancelación, estimación de tiempo
