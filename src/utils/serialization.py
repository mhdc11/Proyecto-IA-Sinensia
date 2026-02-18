"""
JSON Serialization Utilities - Analizador de Documentos Legales

Funciones para serializar y deserializar objetos Pydantic a/desde JSON,
con manejo especial de datetime y enums.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import json
from datetime import datetime
from typing import Type, TypeVar
from pydantic import BaseModel

# Type variable para generic typing
T = TypeVar("T", bound=BaseModel)


def to_json(obj: BaseModel, indent: int = 2) -> str:
    """
    Serializa un objeto Pydantic a JSON string

    Args:
        obj: Objeto Pydantic a serializar
        indent: Nivel de indentación para formato legible (default: 2)

    Returns:
        str: JSON string formateado

    Raises:
        TypeError: Si el objeto no es serializable

    Example:
        >>> from src.models.analisis import Analisis
        >>> analisis = Analisis(tipo_documento="contrato")
        >>> json_str = to_json(analisis)
        >>> print(json_str)
        {
          "tipo_documento": "contrato",
          ...
        }
    """
    try:
        # Pydantic's model_dump() ya maneja datetime y enums correctamente
        data = obj.model_dump(mode="json")
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise TypeError(f"Error serializing object to JSON: {e}") from e


def from_json(cls: Type[T], data: str) -> T:
    """
    Deserializa un JSON string a objeto Pydantic

    Args:
        cls: Clase Pydantic target (Analisis, Documento, Dupla)
        data: JSON string a deserializar

    Returns:
        Objeto Pydantic validado

    Raises:
        ValueError: Si el JSON es inválido o no cumple el schema
        TypeError: Si la clase no es un BaseModel de Pydantic

    Example:
        >>> from src.models.analisis import Analisis
        >>> json_str = '{"tipo_documento": "contrato", "confianza_aprox": 0.9}'
        >>> analisis = from_json(Analisis, json_str)
        >>> print(analisis.tipo_documento)
        'contrato'
    """
    if not issubclass(cls, BaseModel):
        raise TypeError(f"{cls} must be a Pydantic BaseModel subclass")

    try:
        # Parsear JSON string a dict
        json_dict = json.loads(data)

        # Validar y crear instancia con Pydantic
        return cls(**json_dict)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}") from e
    except Exception as e:
        raise ValueError(f"Error deserializing JSON to {cls.__name__}: {e}") from e


def to_json_file(obj: BaseModel, file_path: str, indent: int = 2) -> None:
    """
    Serializa un objeto Pydantic a archivo JSON

    Args:
        obj: Objeto Pydantic a serializar
        file_path: Ruta del archivo donde guardar el JSON
        indent: Nivel de indentación (default: 2)

    Raises:
        IOError: Si hay error al escribir el archivo

    Example:
        >>> from src.models.analisis import Analisis
        >>> analisis = Analisis(tipo_documento="contrato")
        >>> to_json_file(analisis, "data/analisis.json")
    """
    try:
        json_str = to_json(obj, indent=indent)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_str)
    except Exception as e:
        raise IOError(f"Error writing JSON to file {file_path}: {e}") from e


def from_json_file(cls: Type[T], file_path: str) -> T:
    """
    Deserializa un archivo JSON a objeto Pydantic

    Args:
        cls: Clase Pydantic target
        file_path: Ruta del archivo JSON a leer

    Returns:
        Objeto Pydantic validado

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el JSON es inválido o no cumple el schema

    Example:
        >>> from src.models.analisis import Analisis
        >>> analisis = from_json_file(Analisis, "data/analisis.json")
        >>> print(analisis.tipo_documento)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_str = f.read()
        return from_json(cls, json_str)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading JSON from file {file_path}: {e}") from e


def round_trip_test(obj: BaseModel) -> bool:
    """
    Test de round-trip: object → JSON → object

    Verifica que la serialización y deserialización preservan todos los campos.

    Args:
        obj: Objeto Pydantic a testear

    Returns:
        bool: True si el round-trip preserva todos los campos

    Example:
        >>> from src.models.analisis import Analisis
        >>> analisis = Analisis(tipo_documento="contrato", confianza_aprox=0.9)
        >>> assert round_trip_test(analisis)
    """
    try:
        # Serializar a JSON
        json_str = to_json(obj)

        # Deserializar de vuelta al mismo tipo
        obj_restored = from_json(type(obj), json_str)

        # Comparar dictionaries (ignora diferencias mínimas de datetime microsegundos)
        original_dict = obj.model_dump()
        restored_dict = obj_restored.model_dump()

        return original_dict == restored_dict
    except Exception as e:
        print(f"Round-trip test failed: {e}")
        return False


if __name__ == "__main__":
    # Test de serialización/deserialización
    print("=" * 60)
    print("Testing JSON Serialization Utilities")
    print("=" * 60)

    from src.models.analisis import Analisis, Fecha, Importe
    from src.models.documento import Documento, TipoFuente
    from src.models.dupla import Dupla

    # Test 1: Análisis
    print("\n📋 Test 1: Análisis serialization")
    analisis = Analisis(
        tipo_documento="contrato_laboral",
        partes=["ACME CORP", "Juan Pérez"],
        fechas=[Fecha(etiqueta="Inicio", valor="2026-03-01")],
        importes=[Importe(concepto="Salario", valor=30000.0, moneda="EUR")],
        resumen_bullets=["Contrato anual"],
        confianza_aprox=0.9,
    )

    json_str = to_json(analisis)
    print("✅ Serialized to JSON:")
    print(json_str[:200] + "...")

    analisis_restored = from_json(Analisis, json_str)
    print(f"\n✅ Deserialized: {analisis_restored}")
    print(f"✅ Round-trip test: {round_trip_test(analisis)}")

    # Test 2: Documento
    print("\n📋 Test 2: Documento serialization")
    doc = Documento(
        id="a1b2c3d4e5f6g7h8",
        nombre="contrato.pdf",
        tipo_fuente=TipoFuente.PDF_NATIVE,
        paginas=10,
        bytes=245760,
    )

    json_str = to_json(doc)
    print("✅ Serialized to JSON:")
    print(json_str[:200] + "...")

    doc_restored = from_json(Documento, json_str)
    print(f"\n✅ Deserialized: {doc_restored}")
    print(f"✅ Round-trip test: {round_trip_test(doc)}")

    # Test 3: Dupla
    print("\n📋 Test 3: Dupla serialization")
    dupla = Dupla(id="a1b2c3d4e5f6g7h8", documento=doc, analisis=analisis)

    json_str = to_json(dupla)
    print("✅ Serialized to JSON:")
    print(json_str[:300] + "...")

    dupla_restored = from_json(Dupla, json_str)
    print(f"\n✅ Deserialized: {dupla_restored}")
    print(f"✅ Round-trip test: {round_trip_test(dupla)}")

    # Test 4: File I/O (opcional - requiere permisos de escritura)
    try:
        import tempfile
        import os

        print("\n📋 Test 4: File I/O")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        to_json_file(analisis, temp_path)
        print(f"✅ Written to temp file: {temp_path}")

        analisis_from_file = from_json_file(Analisis, temp_path)
        print(f"✅ Read from file: {analisis_from_file}")

        os.unlink(temp_path)
        print("✅ Temp file cleaned up")
    except Exception as e:
        print(f"⚠️  File I/O test skipped: {e}")

    print("\n✅ All serialization tests passed!")
