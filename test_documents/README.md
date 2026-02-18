# Test Documents

Esta carpeta contiene documentos para pruebas del sistema.

## Estructura

```
test_documents/
├── real_docs/          # Documentos reales para pruebas (no versionados)
├── fixtures/           # Documentos de ejemplo simples (versionados)
└── README.md
```

## Cómo Usar

### 1. Añadir Documentos Reales

Copia documentos legales a `real_docs/`:
- 2-3 contratos (PDF nativo)
- 1-2 nóminas (PDF escaneado o nativo)
- 1 convenio o certificado

**IMPORTANTE:** No subir documentos sensibles al repositorio.

### 2. Ejecutar Pruebas

```bash
# Analizar con la aplicación principal
streamlit run src/ui/app.py

# O ejecutar benchmark
python tests/performance/benchmark.py --test-dir test_documents/real_docs --verbose
```

### 3. Revisar Resultados

- Verificar precisión de extracción de texto
- Validar categorías (partes, fechas, importes)
- Comprobar clasificación de tipo_documento
- Medir tiempos de análisis

### 4. Ajustar Prompts

Si el LLM comete errores recurrentes, editar `src/orchestration/prompts.py`.

## Ejemplo de Resultado Esperado

**Documento:** contrato_laboral_10pags.pdf

```
✅ Tipo: contrato_laboral (confianza: 92%)
✅ Partes: 2 detectadas
✅ Fechas: 3 detectadas (inicio, fin, renovación)
✅ Importes: 2 detectados (salario, bonus)
⏱️ Tiempo: 28.3s
```
