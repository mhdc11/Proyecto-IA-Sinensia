# 🗺️ Roadmap - Analizador de Documentos Legales

Funcionalidades planificadas para futuras versiones del sistema.

---

## 📅 Versión Actual: 1.0.0 (MVP)

✅ **Completado:**
- Extracción de texto (PDF, DOCX, imágenes con OCR)
- Análisis con IA local (Ollama)
- 8 categorías estructuradas
- Historial persistente en JSON
- Interfaz Streamlit local
- Exportación JSON
- Privacidad 100% local

---

## 🚀 Versión 1.1.0 - Mejoras de Base de Datos

**Objetivo:** Migrar almacenamiento de JSON a SQLite para mejor escalabilidad.

### Funcionalidades

- [ ] **Migración a SQLite**
  - Tablas: `documentos`, `analisis`, `duplas`, `versiones`
  - Índices en: `id`, `ts_creacion`, `tipo_documento`
  - Función de migración desde `duplas.json` existente

- [ ] **Versionado de Análisis**
  - Guardar múltiples versiones del análisis del mismo documento
  - Comparar cambios entre versiones (diff)
  - Restaurar versión anterior

- [ ] **Búsqueda Avanzada**
  - Búsqueda full-text en contenido de análisis
  - Filtros por: tipo_documento, fechas, partes, importes
  - Exportar resultados de búsqueda

**Estimación:** 2-3 semanas

**Beneficios:**
- Historial escalable (miles de documentos)
- Consultas rápidas
- Integridad referencial

---

## 📊 Versión 1.2.0 - Análisis Avanzado

**Objetivo:** Mejorar precisión y capacidades de análisis.

### Funcionalidades

- [ ] **Clasificación Automática Mejorada**
  - Detección de subcategorías: contrato_laboral, contrato_arrendamiento, contrato_compraventa
  - Confianza por categoría (no solo global)
  - Sugerencias de categorías alternativas

- [ ] **Extracción de Relaciones**
  - Detectar relaciones entre partes (empleador-empleado, arrendador-arrendatario)
  - Vincular importes con fechas (ej: "Salario 30.000 EUR anual desde 2026-03-01")
  - Grafo de dependencias entre obligaciones y derechos

- [ ] **Análisis Comparativo**
  - Comparar dos documentos lado a lado
  - Diff visual de diferencias
  - Resumen de cambios clave

- [ ] **Detección de Cláusulas Estándar**
  - Identificar cláusulas comunes (no competencia, confidencialidad, jurisdicción)
  - Alertar sobre cláusulas anómalas o poco comunes
  - Base de datos de cláusulas típicas por tipo de documento

**Estimación:** 3-4 semanas

**Beneficios:**
- Mayor precisión en análisis
- Identificación de patrones
- Comparación de contratos

---

## 🔍 Versión 1.3.0 - Búsqueda e Historial

**Objetivo:** Mejorar navegación y consulta del historial.

### Funcionalidades

- [ ] **Filtros Avanzados del Historial**
  - Filtrar por: tipo_documento, rango de fechas, partes, estado
  - Ordenar por: confianza, tamaño, fecha de creación
  - Vista de tabla con columnas personalizables

- [ ] **Búsqueda Semántica**
  - Buscar por: "contratos con cláusula de no competencia"
  - Búsqueda por similitud de contenido
  - Autocompletado de términos

- [ ] **Etiquetas y Categorización Manual**
  - Añadir etiquetas personalizadas a documentos
  - Agrupar documentos por proyecto/cliente
  - Notas privadas por análisis

- [ ] **Estadísticas del Historial**
  - Dashboard con métricas: documentos analizados, tipos más comunes, tiempo promedio
  - Gráficos de distribución por tipo, confianza, tamaño
  - Exportar estadísticas en CSV/Excel

**Estimación:** 2-3 semanas

**Beneficios:**
- Gestión eficiente de grandes volúmenes
- Encontrar documentos rápidamente
- Insights del historial

---

## 🌐 Versión 1.4.0 - Multi-idioma y Localización

**Objetivo:** Soportar múltiples idiomas en la interfaz y análisis.

### Funcionalidades

- [ ] **UI Multi-idioma**
  - Español (completo)
  - Inglés (completo)
  - Soporte para otros idiomas (francés, alemán, italiano)

- [ ] **Análisis en Múltiples Idiomas**
  - Configurar idioma de salida independiente del idioma del documento
  - Traducción automática de resultados (opcional, con modelo local)
  - Detección automática de idioma del documento

- [ ] **Formatos Regionales**
  - Fechas: DD/MM/YYYY (EU) vs MM/DD/YYYY (US) vs YYYY-MM-DD (ISO)
  - Monedas: EUR, USD, GBP con símbolos regionales
  - Números: separador de miles y decimales por región

**Estimación:** 2 semanas

**Beneficios:**
- Alcance internacional
- Documentos multinacionales
- Mejor UX regional

---

## ⚡ Versión 1.5.0 - Optimización y Rendimiento

**Objetivo:** Mejorar velocidad y eficiencia del sistema.

### Funcionalidades

- [ ] **Procesamiento Paralelo**
  - Analizar múltiples documentos en paralelo (ThreadPool)
  - Cola de trabajos con prioridad
  - Cancelación de análisis en curso

- [ ] **Cache de Análisis**
  - Detectar documentos ya analizados por hash
  - Mostrar resultado en caché instantáneamente
  - Opción "Forzar re-análisis"

- [ ] **Modelos Optimizados**
  - Soportar modelos cuantizados (GGUF) para menor uso de RAM
  - Configuración de GPU explícita (CUDA, Metal)
  - Perfiles de rendimiento: Rápido, Balanceado, Preciso

- [ ] **OCR Incremental**
  - Solo ejecutar OCR en páginas sin texto
  - Procesar páginas independientemente
  - Resumir OCR en tiempo real

**Estimación:** 2-3 semanas

**Beneficios:**
- Análisis más rápido
- Menor uso de recursos
- Experiencia más fluida

---

## 📱 Versión 2.0.0 - Extensiones y Ecosistema

**Objetivo:** Expandir capacidades y opciones de integración.

### Funcionalidades

- [ ] **API REST**
  - Endpoints para: /analyze, /history, /search
  - Autenticación con tokens
  - Documentación OpenAPI/Swagger

- [ ] **CLI (Command-Line Interface)**
  - `doc-analyzer analyze documento.pdf --output json`
  - Integración en scripts y pipelines
  - Modo batch para múltiples archivos

- [ ] **Plugins y Extensiones**
  - Sistema de plugins para extractores personalizados
  - Hooks para post-procesamiento
  - Plantillas de análisis por dominio

- [ ] **Integración con Servicios**
  - Exportar a Google Drive / Dropbox (opcional)
  - Sincronización entre dispositivos (local-first)
  - Webhooks para notificaciones

- [ ] **Aplicación de Escritorio**
  - Empaquetado con PyInstaller / Electron
  - Instalador nativo para Windows/macOS/Linux
  - Menú de sistema y atajos de teclado

**Estimación:** 4-6 semanas

**Beneficios:**
- Integración en workflows
- Automatización
- Ecosistema extensible

---

## 🔐 Versión 2.1.0 - Seguridad y Compliance

**Objetivo:** Reforzar seguridad y cumplimiento normativo.

### Funcionalidades

- [ ] **Cifrado de Historial**
  - Cifrar `duplas.json` con contraseña
  - Opción de borrado seguro (múltiples pasadas)
  - Auto-bloqueo tras inactividad

- [ ] **Auditoría**
  - Log de acciones: análisis realizado, documento exportado, historial limpiado
  - Exportar auditoría en formato inmutable
  - Integridad con hashes SHA-256

- [ ] **Modo Privado**
  - No guardar en historial (análisis volátil)
  - Eliminar archivos temporales automáticamente
  - Indicador visual de modo privado activo

- [ ] **Cumplimiento GDPR/RGPD**
  - Derecho al olvido: eliminar completamente análisis
  - Exportar datos de usuario en formato estándar
  - Consentimiento explícito para almacenamiento

**Estimación:** 2-3 semanas

**Beneficios:**
- Cumplimiento normativo
- Mayor confianza del usuario
- Protección de datos sensibles

---

## 🧠 Versión 3.0.0 - IA Avanzada (Futuro Lejano)

**Objetivo:** Capacidades de IA de próxima generación.

### Ideas Explorar

- **Fine-tuning de Modelos**
  - Entrenar modelo específico para dominio legal español
  - Incorporar feedback del usuario para mejorar precisión

- **Análisis Predictivo**
  - Predecir riesgos basados en patrones históricos
  - Sugerir cláusulas faltantes

- **Extracción de Imágenes**
  - Detectar firmas, sellos, logotipos
  - OCR de tablas complejas
  - Extracción de gráficos y diagramas

- **Asistente Conversacional**
  - Chat con el documento: "¿Cuál es la fecha de vencimiento?"
  - Preguntas sobre el análisis
  - Generación de resúmenes personalizados

**Estimación:** TBD (investigación requerida)

---

## 🎯 Priorización

| Prioridad | Versión | Justificación |
|-----------|---------|---------------|
| 🔴 Alta | 1.1.0 - SQLite | Escalabilidad crítica |
| 🟠 Media | 1.2.0 - Análisis Avanzado | Mejora de valor |
| 🟠 Media | 1.3.0 - Búsqueda | Usabilidad con grandes historiales |
| 🟡 Baja | 1.4.0 - Multi-idioma | Casos de uso específicos |
| 🟡 Baja | 1.5.0 - Rendimiento | Optimización incremental |
| 🟢 Futura | 2.0.0+ | Expansión del ecosistema |

---

## 📝 Cómo Contribuir a este Roadmap

¿Tienes una idea para una funcionalidad?

1. **Abre un issue** en GitHub con etiqueta `enhancement`
2. Describe: problema que resuelve, usuarios beneficiados, complejidad estimada
3. La comunidad votará (👍) las propuestas más populares
4. Las funcionalidades con más votos se priorizarán

**Ideas en discusión:**
- Integración con sistemas de gestión documental (DMS)
- Reconocimiento de tablas en PDFs
- Modo colaborativo (múltiples usuarios, mismo historial)
- Análisis de audio (transcripción + análisis)

---

## 📊 Métricas de Éxito

Para cada versión, medir:

- ⏱️ **Tiempo de análisis** (objetivo: < 20s para 10 páginas)
- 🎯 **Precisión** (objetivo: > 90% categorías correctas)
- 😊 **Satisfacción de usuario** (encuestas post-uso)
- 🐛 **Bugs reportados** (objetivo: < 5 críticos por release)
- 📦 **Adopción** (descargas, estrellas en GitHub)

---

**Última actualización:** 2026-02-18

**¿Preguntas sobre el roadmap?** Únete a las [Discussions](https://github.com/yourusername/analizador-documentos-legales/discussions).
