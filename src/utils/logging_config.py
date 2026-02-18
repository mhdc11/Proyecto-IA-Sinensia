"""
Logging Configuration and Timing Utilities - Analizador de Documentos Legales

Configura logging básico y proporciona utilidades para medir tiempos
de operaciones del pipeline de análisis.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager


# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None
) -> logging.Logger:
    """
    Configura logging básico para la aplicación

    Args:
        level: Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: Path opcional para guardar logs en archivo
        log_format: Formato personalizado de logs
        date_format: Formato personalizado de fechas

    Returns:
        logging.Logger: Logger configurado

    Example:
        >>> from pathlib import Path
        >>> logger = setup_logging(level="INFO", log_file=Path("logs/app.log"))
        >>> logger.info("Application started")
    """
    # Mapeo de niveles
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    log_level = level_map.get(level.upper(), logging.INFO)

    # Formato
    formatter = logging.Formatter(
        fmt=log_format or DEFAULT_LOG_FORMAT,
        datefmt=date_format or DEFAULT_DATE_FORMAT
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpiar handlers existentes
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (opcional)
    if log_file:
        # Crear directorio si no existe
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            filename=log_file,
            mode="a",
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"Logging to file: {log_file}")

    return root_logger


class Timer:
    """
    Utilidad para medir tiempos de ejecución de operaciones

    Example:
        >>> timer = Timer("OCR Processing")
        >>> timer.start()
        >>> # ... operación ...
        >>> elapsed = timer.stop()  # Returns elapsed time in seconds
        >>> timer.log()  # Logs the elapsed time
    """

    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """
        Args:
            operation_name: Nombre descriptivo de la operación
            logger: Logger opcional (usa logger raíz si no se especifica)
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: Optional[float] = None

    def start(self) -> None:
        """Inicia el timer"""
        self.start_time = time.time()
        self.logger.debug(f"⏱️  Started: {self.operation_name}")

    def stop(self) -> float:
        """
        Detiene el timer y retorna el tiempo transcurrido

        Returns:
            float: Tiempo transcurrido en segundos
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started. Call start() first.")

        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        return self.elapsed

    def log(self, level: str = "INFO") -> None:
        """
        Registra el tiempo transcurrido en el log

        Args:
            level: Nivel de log ('DEBUG', 'INFO', 'WARNING', etc.)
        """
        if self.elapsed is None:
            raise RuntimeError("Timer not stopped. Call stop() first.")

        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"⏱️  {self.operation_name}: {self.elapsed:.2f}s")

    def __repr__(self) -> str:
        status = "not started" if self.start_time is None else \
                 "running" if self.end_time is None else \
                 f"completed ({self.elapsed:.2f}s)"
        return f"Timer('{self.operation_name}', {status})"


@contextmanager
def timed_operation(
    operation_name: str,
    logger: Optional[logging.Logger] = None,
    log_level: str = "INFO"
):
    """
    Context manager para medir tiempos de operaciones con logs automáticos

    Args:
        operation_name: Nombre descriptivo de la operación
        logger: Logger opcional
        log_level: Nivel de log para el mensaje final

    Yields:
        Timer: Timer object (puede ser ignorado)

    Example:
        >>> with timed_operation("Text Extraction"):
        ...     texto = extract_text(file)
        # Automáticamente logs: "⏱️  Text Extraction: 1.23s"
    """
    timer = Timer(operation_name, logger)
    timer.start()

    try:
        yield timer
    finally:
        timer.stop()
        timer.log(level=log_level)


class PipelineMetrics:
    """
    Acumula métricas de un pipeline completo con múltiples etapas

    Example:
        >>> metrics = PipelineMetrics("Document Analysis")
        >>> metrics.start_stage("Extraction")
        >>> # ... operación ...
        >>> metrics.end_stage("Extraction")
        >>> metrics.start_stage("LLM Analysis")
        >>> # ... operación ...
        >>> metrics.end_stage("LLM Analysis")
        >>> metrics.log_summary()
        # Logs summary with total time and stage breakdown
    """

    def __init__(self, pipeline_name: str, logger: Optional[logging.Logger] = None):
        """
        Args:
            pipeline_name: Nombre del pipeline
            logger: Logger opcional
        """
        self.pipeline_name = pipeline_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.stages: Dict[str, float] = {}
        self.current_stage: Optional[str] = None
        self.current_stage_start: Optional[float] = None

    def start(self) -> None:
        """Inicia el pipeline"""
        self.start_time = time.time()
        self.logger.info(f"🚀 Pipeline started: {self.pipeline_name}")

    def start_stage(self, stage_name: str) -> None:
        """Inicia una etapa del pipeline"""
        if self.current_stage is not None:
            # Auto-end previous stage
            self.end_stage(self.current_stage)

        self.current_stage = stage_name
        self.current_stage_start = time.time()
        self.logger.debug(f"  ▶️  Stage: {stage_name}")

    def end_stage(self, stage_name: Optional[str] = None) -> None:
        """Finaliza la etapa actual del pipeline"""
        if self.current_stage_start is None:
            return

        stage_to_end = stage_name or self.current_stage
        if stage_to_end is None:
            return

        elapsed = time.time() - self.current_stage_start
        self.stages[stage_to_end] = elapsed
        self.logger.debug(f"  ✅ {stage_to_end}: {elapsed:.2f}s")

        self.current_stage = None
        self.current_stage_start = None

    def end(self) -> float:
        """
        Finaliza el pipeline y retorna el tiempo total

        Returns:
            float: Tiempo total en segundos
        """
        if self.current_stage is not None:
            # Auto-end current stage
            self.end_stage()

        if self.start_time is None:
            raise RuntimeError("Pipeline not started")

        self.end_time = time.time()
        return self.end_time - self.start_time

    def log_summary(self) -> None:
        """Registra un resumen completo con todas las etapas"""
        if self.end_time is None:
            total_time = time.time() - (self.start_time or time.time())
        else:
            total_time = self.end_time - (self.start_time or 0)

        self.logger.info("=" * 60)
        self.logger.info(f"📊 Pipeline Summary: {self.pipeline_name}")
        self.logger.info("=" * 60)

        if self.stages:
            for stage_name, stage_time in self.stages.items():
                percentage = (stage_time / total_time) * 100 if total_time > 0 else 0
                self.logger.info(f"  {stage_name}: {stage_time:.2f}s ({percentage:.1f}%)")

        self.logger.info(f"  TOTAL: {total_time:.2f}s")
        self.logger.info("=" * 60)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas como diccionario

        Returns:
            Dict con total_time y stages
        """
        total_time = (self.end_time or time.time()) - (self.start_time or time.time())

        return {
            "pipeline_name": self.pipeline_name,
            "total_time": total_time,
            "stages": dict(self.stages),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test de logging y timing
    print("=" * 60)
    print("Testing Logging Configuration and Timing")
    print("=" * 60)

    # Setup logging
    logger = setup_logging(level="INFO")

    # Test 1: Timer básico
    print("\n📋 Test 1: Basic Timer")
    timer = Timer("Test Operation", logger)
    timer.start()
    time.sleep(0.5)  # Simular operación
    elapsed = timer.stop()
    timer.log()

    # Test 2: Context manager
    print("\n📋 Test 2: Context Manager")
    with timed_operation("Simulated Extraction", logger):
        time.sleep(0.3)

    # Test 3: Pipeline metrics
    print("\n📋 Test 3: Pipeline Metrics")
    metrics = PipelineMetrics("Document Analysis Pipeline", logger)
    metrics.start()

    metrics.start_stage("Extraction")
    time.sleep(0.2)
    metrics.end_stage()

    metrics.start_stage("Normalization")
    time.sleep(0.1)
    metrics.end_stage()

    metrics.start_stage("LLM Analysis")
    time.sleep(0.5)
    metrics.end_stage()

    metrics.start_stage("Post-processing")
    time.sleep(0.1)
    metrics.end_stage()

    total = metrics.end()
    metrics.log_summary()

    # Test 4: Get metrics dict
    print("\n📋 Test 4: Get Metrics Dict")
    metrics_dict = metrics.get_metrics()
    print(f"Total: {metrics_dict['total_time']:.2f}s")
    print(f"Stages: {len(metrics_dict['stages'])}")

    print("\n✅ Logging and timing utilities ready!")
