"""
JSON History Store - Analizador de Documentos Legales

Persistencia del historial de duplas en archivo JSON local con funciones
de guardado/carga, manejo de corrupción y política de reemplazo.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.models.dupla import Dupla
from src.utils.serialization import to_json, from_json

logger = logging.getLogger(__name__)


# Ruta por defecto para el historial
DEFAULT_HISTORY_PATH = Path("data/duplas.json")


class HistoryCorruptedError(Exception):
    """Excepción cuando el archivo de historial está corrupto"""
    pass


def ensure_history_file(path: Path) -> None:
    """
    Asegura que el archivo de historial y su directorio existen

    Args:
        path: Ruta al archivo de historial

    Example:
        >>> ensure_history_file(Path("data/duplas.json"))
    """
    # Crear directorio si no existe
    path.parent.mkdir(parents=True, exist_ok=True)

    # Crear archivo vacío si no existe
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)
        logger.info(f"Created new history file: {path}")


def save_history(
    duplas: List[Dupla],
    path: Optional[Path] = None,
    pretty: bool = True
) -> None:
    """
    Guarda historial de duplas en archivo JSON

    Args:
        duplas: Lista de duplas a guardar
        path: Ruta al archivo (default: data/duplas.json)
        pretty: Si True, formatea JSON con indentación (default: True)

    Raises:
        IOError: Si no se puede escribir el archivo

    Example:
        >>> save_history(duplas, Path("data/duplas.json"))
    """
    if path is None:
        path = DEFAULT_HISTORY_PATH

    ensure_history_file(path)

    try:
        # Convertir duplas a diccionarios
        duplas_dict = [dupla.model_dump() for dupla in duplas]

        # Guardar con formato legible
        with open(path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(duplas_dict, f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(duplas_dict, f, ensure_ascii=False, default=str)

        logger.info(f"Saved history: {len(duplas)} duplas to {path}")

    except Exception as e:
        logger.error(f"Failed to save history to {path}: {e}")
        raise IOError(f"Could not save history: {e}") from e


def load_history(path: Optional[Path] = None) -> List[Dupla]:
    """
    Carga historial de duplas desde archivo JSON

    Args:
        path: Ruta al archivo (default: data/duplas.json)

    Returns:
        List[Dupla]: Lista de duplas cargadas (vacía si no existe o está corrupto)

    Note:
        Si el archivo está corrupto, retorna lista vacía y crea backup

    Example:
        >>> duplas = load_history(Path("data/duplas.json"))
        >>> print(len(duplas))
        5
    """
    if path is None:
        path = DEFAULT_HISTORY_PATH

    # Si no existe, crear vacío
    if not path.exists():
        ensure_history_file(path)
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            duplas_dict = json.load(f)

        # Validar que sea una lista
        if not isinstance(duplas_dict, list):
            raise HistoryCorruptedError("History file is not a list")

        # Convertir a objetos Dupla
        duplas = []
        for i, dupla_dict in enumerate(duplas_dict):
            try:
                dupla = Dupla(**dupla_dict)
                duplas.append(dupla)
            except Exception as e:
                logger.warning(f"Skipping corrupted dupla at index {i}: {e}")
                continue

        logger.info(f"Loaded history: {len(duplas)} duplas from {path}")
        return duplas

    except json.JSONDecodeError as e:
        logger.error(f"History file corrupted (invalid JSON): {path} - {e}")

        # Crear backup del archivo corrupto
        backup_path = path.with_suffix(f".corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            path.rename(backup_path)
            logger.info(f"Backed up corrupted file to: {backup_path}")
        except Exception:
            pass

        # Crear nuevo archivo vacío
        ensure_history_file(path)
        return []

    except Exception as e:
        logger.error(f"Failed to load history from {path}: {e}")
        return []


def add_to_history(
    dupla: Dupla,
    path: Optional[Path] = None,
    policy: str = "replace"
) -> List[Dupla]:
    """
    Añade una dupla al historial con política de reemplazo

    Args:
        dupla: Dupla a añadir
        path: Ruta al archivo de historial
        policy: Política de reemplazo para IDs duplicados
                - "replace": Reemplaza la dupla existente con el mismo ID
                - "version": Crea nueva versión con timestamp en el ID

    Returns:
        List[Dupla]: Historial actualizado

    Example:
        >>> new_history = add_to_history(dupla, policy="replace")
    """
    if path is None:
        path = DEFAULT_HISTORY_PATH

    # Cargar historial actual
    history = load_history(path)

    # Buscar dupla con mismo ID
    existing_index = next(
        (i for i, d in enumerate(history) if d.id == dupla.id),
        None
    )

    if existing_index is not None:
        if policy == "replace":
            # Reemplazar la dupla existente
            history[existing_index] = dupla
            logger.info(f"Replaced existing dupla with ID: {dupla.id}")

        elif policy == "version":
            # Crear nueva versión con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dupla.id = f"{dupla.id}_{timestamp}"
            dupla.analisis.notas.append(
                f"Versión {timestamp} del documento original (re-analizado)"
            )
            history.append(dupla)
            logger.info(f"Created new version with ID: {dupla.id}")

        else:
            raise ValueError(f"Invalid policy: {policy}. Use 'replace' or 'version'")

    else:
        # ID no existe, simplemente añadir
        history.append(dupla)
        logger.info(f"Added new dupla with ID: {dupla.id}")

    # Guardar historial actualizado
    save_history(history, path)

    return history


def remove_from_history(
    dupla_id: str,
    path: Optional[Path] = None
) -> List[Dupla]:
    """
    Elimina una dupla del historial por su ID

    Args:
        dupla_id: ID de la dupla a eliminar
        path: Ruta al archivo de historial

    Returns:
        List[Dupla]: Historial actualizado

    Example:
        >>> updated_history = remove_from_history("abc123456789abcd")
    """
    if path is None:
        path = DEFAULT_HISTORY_PATH

    # Cargar historial
    history = load_history(path)

    # Filtrar la dupla a eliminar
    original_count = len(history)
    history = [d for d in history if d.id != dupla_id]

    if len(history) < original_count:
        logger.info(f"Removed dupla with ID: {dupla_id}")
        save_history(history, path)
    else:
        logger.warning(f"Dupla with ID {dupla_id} not found in history")

    return history


def clear_history(path: Optional[Path] = None) -> None:
    """
    Limpia completamente el historial

    Args:
        path: Ruta al archivo de historial

    Example:
        >>> clear_history()
    """
    if path is None:
        path = DEFAULT_HISTORY_PATH

    save_history([], path)
    logger.info("History cleared")


if __name__ == "__main__":
    # Test del módulo de persistencia
    print("=" * 60)
    print("Testing JSON History Store")
    print("=" * 60)

    from src.models.documento import Documento, TipoFuente
    from src.models.analisis import Analisis, Fecha, Importe
    from src.models.dupla import Dupla, EstadoDupla

    # Test path
    test_path = Path("data/test_duplas.json")

    # Test 1: Crear y guardar dupla
    print("\n📋 Test 1: Save history")

    documento = Documento(
        id="test123456789abc",
        nombre="test_doc.pdf",
        tipo_fuente=TipoFuente.PDF_NATIVE,
        paginas=5,
        bytes=100000,
        idioma_detectado="es",
        ts_ingesta=datetime.now()
    )

    analisis = Analisis(
        tipo_documento="contrato",
        partes=["ACME Corp", "Juan Pérez"],
        fechas=[Fecha(etiqueta="Inicio", valor="2026-03-01")],
        importes=[Importe(concepto="Salario", valor=30000.0, moneda="EUR")],
        obligaciones=["No competir"],
        derechos=["30 días vacaciones"],
        riesgos=["Cláusula no competencia"],
        resumen_bullets=["Contrato anual"],
        confianza_aprox=0.9
    )

    dupla = Dupla(
        id=documento.id,
        documento=documento,
        analisis=analisis,
        ts_creacion=datetime.now(),
        ts_actualizacion=datetime.now(),
        estado=EstadoDupla.VALIDO
    )

    save_history([dupla], test_path)
    print(f"✅ Saved 1 dupla to {test_path}")

    # Test 2: Cargar historial
    print("\n📋 Test 2: Load history")
    loaded = load_history(test_path)
    print(f"✅ Loaded {len(loaded)} duplas")
    print(f"   First dupla ID: {loaded[0].id}")

    # Test 3: Añadir con política "replace"
    print("\n📋 Test 3: Add with 'replace' policy")
    dupla.analisis.confianza_aprox = 0.95  # Modificar
    updated = add_to_history(dupla, test_path, policy="replace")
    print(f"✅ History size: {len(updated)} (should be 1)")
    print(f"   Confidence: {updated[0].analisis.confianza_aprox}")

    # Test 4: Añadir con política "version"
    print("\n📋 Test 4: Add with 'version' policy")
    updated = add_to_history(dupla, test_path, policy="version")
    print(f"✅ History size: {len(updated)} (should be 2)")
    print(f"   IDs: {[d.id for d in updated]}")

    # Test 5: Eliminar dupla
    print("\n📋 Test 5: Remove dupla")
    updated = remove_from_history(dupla.id, test_path)
    print(f"✅ History size after removal: {len(updated)}")

    # Test 6: Limpiar historial
    print("\n📋 Test 6: Clear history")
    clear_history(test_path)
    loaded = load_history(test_path)
    print(f"✅ History size after clear: {len(loaded)}")

    # Cleanup
    if test_path.exists():
        test_path.unlink()

    print("\n✅ JSON History Store ready!")
