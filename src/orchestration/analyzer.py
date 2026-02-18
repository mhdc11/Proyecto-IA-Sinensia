"""
Unified Analysis Service - Analizador de Documentos Legales

Orquesta el pipeline completo de análisis:
extracción → normalización → prompt → LLM → validación → post-procesado → dupla

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

from src.models.analisis import Analisis
from src.models.documento import Documento, TipoFuente
from src.models.dupla import Dupla, EstadoDupla
from src.extractors import extract_text_auto
from src.utils.text_normalizer import normalize_text
from src.utils.hashing import compute_file_hash, compute_doc_meta
from src.utils.config_loader import get_config
from src.orchestration.ollama_client import OllamaClient
from src.orchestration.prompt_builder import build_prompt
from src.orchestration.json_validator import retry_with_correction
from src.orchestration.postprocessor import postprocess_analysis
from src.orchestration.chunker import split_text, consolidate_analyses
from src.utils.document_classifier import refine_document_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Base exception for analysis pipeline errors"""
    pass


class ExtractionError(AnalysisError):
    """Error during text extraction"""
    pass


class LLMError(AnalysisError):
    """Error during LLM generation"""
    pass


class ValidationError(AnalysisError):
    """Error during JSON validation"""
    pass


class CancelledException(AnalysisError):
    """Analysis was cancelled by user"""
    pass


def analyze_document(
    file_path: Path,
    force_ocr: bool = False,
    max_chunk_pages: int = 10,
    cancellation_token: Optional[threading.Event] = None
) -> Tuple[Documento, Analisis, Dupla]:
    """
    Pipeline completo de análisis de un documento

    Etapas:
    1. Extracción de texto (con fallback OCR si necesario)
    2. Normalización del texto
    3. Decisión de chunking (si >max_chunk_pages)
    4. Construcción de prompt(s)
    5. Llamada a LLM local (Ollama)
    6. Validación y parsing de JSON
    7. Post-procesamiento (confianza + notas)
    8. Consolidación (si hubo chunks)
    9. Creación de Documento, Analisis, Dupla

    Args:
        file_path: Ruta al documento a analizar
        force_ocr: Forzar OCR incluso en PDFs nativos
        max_chunk_pages: Máximo de páginas por chunk (default: 10)
        cancellation_token: threading.Event para cancelar procesamiento gracefully

    Returns:
        Tuple[Documento, Analisis, Dupla, str]: Documento, Analisis, Dupla y texto original del documento

    Raises:
        ExtractionError: Si falla la extracción de texto
        LLMError: Si el LLM no responde o falla tras reintentos
        ValidationError: Si el JSON no puede validarse tras reintentos
        CancelledException: Si el usuario cancela el procesamiento

    Example:
        >>> from pathlib import Path
        >>> import threading
        >>> cancel_token = threading.Event()
        >>> doc, analisis, dupla = analyze_document(Path("contrato.pdf"), cancellation_token=cancel_token)
        >>> print(analisis.tipo_documento)
        'contrato_laboral'
        >>> print(dupla.estado)
        EstadoDupla.VALIDO
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Starting analysis for: {file_path.name}")

    # Cargar configuración
    config = get_config()

    # Helper para verificar cancelación
    def check_cancellation():
        """Verifica si el usuario ha cancelado el procesamiento"""
        if cancellation_token and cancellation_token.is_set():
            logger.warning(f"⏹ Analysis cancelled by user for: {file_path.name}")
            raise CancelledException(f"Analysis cancelled for {file_path.name}")

    # ========================================================================
    # ETAPA 1: Extracción de texto
    # ========================================================================
    check_cancellation()  # Check before starting
    logger.info("⏳ Stage 1/9: Text extraction")

    try:
        texto_raw, paginas, tipo_fuente = extract_text_auto(
            file_path=file_path,
            ocr_dpi=config.ocr.dpi,
            ocr_lang=config.ocr.languages,
            force_ocr=force_ocr
        )
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise ExtractionError(f"Failed to extract text from {file_path.name}: {e}") from e

    if not texto_raw or len(texto_raw.strip()) == 0:
        raise ExtractionError(f"Extracted text is empty for {file_path.name}")

    logger.info(f"✅ Extracted {len(texto_raw)} chars from {paginas or '?'} pages ({tipo_fuente})")
    check_cancellation()  # Check after extraction

    # ========================================================================
    # ETAPA 2: Normalización
    # ========================================================================
    logger.info("⏳ Stage 2/9: Text normalization")

    texto_normalizado = normalize_text(texto_raw, preserve_structure=True)

    logger.info(f"✅ Normalized to {len(texto_normalizado)} chars")
    check_cancellation()  # Check after normalization

    # ========================================================================
    # ETAPA 3: Decisión de chunking
    # ========================================================================
    logger.info("⏳ Stage 3/9: Chunking decision")

    # Heurística: si >10 páginas O >30,000 chars, hacer chunking
    needs_chunking = (paginas and paginas > max_chunk_pages) or len(texto_normalizado) > 30000

    if needs_chunking:
        logger.info(f"📄 Document requires chunking ({paginas} pages, {len(texto_normalizado)} chars)")
        chunks = split_text(texto_normalizado, max_chunk_size=12000, overlap=200)
        logger.info(f"✅ Split into {len(chunks)} chunks")
    else:
        chunks = [texto_normalizado]
        logger.info(f"✅ No chunking needed (single fragment)")

    check_cancellation()  # Check after chunking decision

    # ========================================================================
    # ETAPA 4-8: Análisis por chunk
    # ========================================================================
    ollama_client = OllamaClient()

    # Verificar salud de Ollama
    if not ollama_client.is_healthy():
        raise LLMError(
            "Ollama is not running. Please start it with: ollama serve"
        )

    analisis_chunks = []

    for i, chunk in enumerate(chunks):
        check_cancellation()  # Check before each chunk
        logger.info(f"⏳ Analyzing chunk {i+1}/{len(chunks)}")

        # Etapa 4: Construcción de prompt
        logger.info(f"  Stage 4/9: Building prompt for chunk {i+1}")
        try:
            prompt = build_prompt(
                texto=chunk,
                max_tokens=config.ollama.max_tokens,
                include_truncation_note=True
            )
        except Exception as e:
            logger.error(f"Prompt building failed: {e}")
            raise ValidationError(f"Failed to build prompt: {e}") from e

        # Etapa 5-7: LLM + Validación con reintentos
        logger.info(f"  Stage 5-7/9: Calling LLM and validating JSON for chunk {i+1}")
        try:
            analisis_chunk, attempts = retry_with_correction(
                llm_function=ollama_client.ollama_generate,
                model=config.ollama.model,
                original_prompt=prompt,
                temperature=config.ollama.temperature,
                max_retries=config.ollama.max_retries
            )
        except RuntimeError as e:
            logger.error(f"LLM generation/validation failed after retries: {e}")
            raise LLMError(f"LLM failed for chunk {i+1}: {e}") from e

        logger.info(f"  ✅ Chunk {i+1} analyzed successfully (took {attempts} attempts)")

        # Etapa 8: Post-procesamiento
        logger.info(f"  Stage 8/9: Post-processing chunk {i+1}")
        analisis_chunk = postprocess_analysis(analisis_chunk, chunk)

        analisis_chunks.append(analisis_chunk)

    # ========================================================================
    # ETAPA 9: Consolidación (si hubo chunks)
    # ========================================================================
    logger.info("⏳ Stage 9/9: Consolidation")

    if len(analisis_chunks) > 1:
        logger.info(f"📊 Consolidating {len(analisis_chunks)} chunk analyses")
        analisis_final = consolidate_analyses(analisis_chunks)
        logger.info("✅ Consolidation complete")
    else:
        analisis_final = analisis_chunks[0]
        logger.info("✅ Single chunk, no consolidation needed")

    check_cancellation()  # Check after consolidation

    # ========================================================================
    # REFINAMIENTO DE TIPO_DOCUMENTO (heurísticas por keywords)
    # ========================================================================
    logger.info("⏳ Refining document type with keyword-based heuristics")
    tipo_original = analisis_final.tipo_documento
    tipo_refinado, confianza_refinada = refine_document_type(
        analisis_final.tipo_documento,
        texto_completo  # Usar texto completo para mejor detección
    )

    if tipo_refinado != tipo_original:
        logger.info(
            f"📝 Document type refined: {tipo_original} → {tipo_refinado} "
            f"(confidence: {confianza_refinada:.2f})"
        )
        analisis_final.tipo_documento = tipo_refinado
        analisis_final.confianza_aprox = confianza_refinada
    else:
        logger.info(f"✅ Document type confirmed: {tipo_original} (confidence: {confianza_refinada:.2f})")

    # ========================================================================
    # Creación de objetos: Documento, Dupla
    # ========================================================================
    logger.info("⏳ Creating Documento and Dupla objects")

    # Documento
    doc_meta = compute_doc_meta(file_path)

    documento = Documento(
        id=doc_meta["id"],
        nombre=file_path.name,
        tipo_fuente=TipoFuente(tipo_fuente),
        paginas=paginas,
        bytes=doc_meta["bytes"],
        idioma_detectado=None,  # TODO: Implementar detección de idioma (T025)
        ts_ingesta=datetime.now()
    )

    # Estado de dupla basado en advertencias
    tiene_advertencias = any("⚠️" in nota for nota in analisis_final.notas)
    completitud = sum([
        bool(analisis_final.partes),
        bool(analisis_final.fechas),
        bool(analisis_final.importes),
        bool(analisis_final.obligaciones),
        bool(analisis_final.derechos),
        bool(analisis_final.riesgos),
        bool(analisis_final.resumen_bullets)
    ]) / 7.0

    if completitud < 0.5:
        estado = EstadoDupla.INCOMPLETO
    elif tiene_advertencias or analisis_final.confianza_aprox < 0.6:
        estado = EstadoDupla.CON_ADVERTENCIAS
    else:
        estado = EstadoDupla.VALIDO

    # Dupla
    dupla = Dupla(
        id=documento.id,
        documento=documento,
        analisis=analisis_final,
        ts_creacion=datetime.now(),
        ts_actualizacion=datetime.now(),
        estado=estado
    )

    logger.info(f"✅ Analysis complete for {file_path.name}")
    logger.info(f"   Type: {analisis_final.tipo_documento}")
    logger.info(f"   Confidence: {analisis_final.confianza_aprox}")
    logger.info(f"   State: {estado.value}")

    return documento, analisis_final, dupla, texto_completo


if __name__ == "__main__":
    # Test del servicio de análisis
    print("=" * 60)
    print("Testing Unified Analysis Service")
    print("=" * 60)

    # Requiere:
    # 1. Ollama running (ollama serve)
    # 2. Modelo llama3.2:3b instalado
    # 3. Documento de prueba

    test_file = Path("tests/fixtures/sample_contract.pdf")

    if not test_file.exists():
        print("⚠️  Test file not found. Please create:")
        print(f"    {test_file.absolute()}")
        print("\nTo run full end-to-end test:")
        print("  1. Start Ollama: ollama serve")
        print("  2. Install model: ollama pull llama3.2:3b")
        print("  3. Create test PDF in tests/fixtures/")
        print("  4. Run: python -m src.orchestration.analyzer")
    else:
        print(f"\n📄 Analyzing: {test_file.name}")
        try:
            documento, analisis, dupla = analyze_document(test_file)

            print("\n✅ Analysis successful!")
            print(f"\nDocumento ID: {documento.id}")
            print(f"Type: {documento.tipo_fuente.value}")
            print(f"Pages: {documento.paginas}")
            print(f"\nAnalysis Type: {analisis.tipo_documento}")
            print(f"Parties: {len(analisis.partes)}")
            print(f"Dates: {len(analisis.fechas)}")
            print(f"Amounts: {len(analisis.importes)}")
            print(f"Obligations: {len(analisis.obligaciones)}")
            print(f"Rights: {len(analisis.derechos)}")
            print(f"Risks: {len(analisis.riesgos)}")
            print(f"Summary bullets: {len(analisis.resumen_bullets)}")
            print(f"Confidence: {analisis.confianza_aprox}")
            print(f"\nDupla State: {dupla.estado.value}")

            if analisis.notas:
                print(f"\nNotes:")
                for nota in analisis.notas:
                    print(f"  - {nota}")

        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
