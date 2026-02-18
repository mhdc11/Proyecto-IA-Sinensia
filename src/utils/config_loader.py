"""
Configuration Loader - Analizador de Documentos Legales

Carga configuración desde archivos YAML y variables de entorno,
proporcionando valores por defecto seguros.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, validator


class OllamaConfig(BaseModel):
    """Configuración de Ollama LLM"""

    endpoint: str = Field(default="http://localhost:11434", description="Ollama API endpoint")
    health_check_timeout: int = Field(default=5, ge=1, le=30, description="Health check timeout (seconds)")
    model: str = Field(default="llama3.2:3b", description="Ollama model name")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(default=4000, ge=1000, le=10000, description="Context window size")
    max_retries: int = Field(default=2, ge=0, le=5, description="Max retries for invalid JSON")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="Retry delay (seconds)")


class OCRConfig(BaseModel):
    """Configuración de OCR"""

    enabled: bool = Field(default=True, description="Enable OCR processing")
    dpi: int = Field(default=300, ge=200, le=600, description="OCR DPI resolution")
    languages: str = Field(default="spa", description="OCR language(s)")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Min OCR confidence")


class ChunkingConfig(BaseModel):
    """Configuración de chunking para documentos largos"""

    enabled: bool = Field(default=True, description="Enable chunking for long documents")
    max_chunk_size: int = Field(default=3500, ge=1000, le=8000, description="Max chunk size (tokens)")
    overlap: int = Field(default=200, ge=0, le=1000, description="Chunk overlap (tokens)")


class ExportConfig(BaseModel):
    """Configuración de exportación"""

    enabled: bool = Field(default=True, description="Enable export functionality")
    default_format: str = Field(default="json", description="Default export format")
    include_metadata: bool = Field(default=True, description="Include metadata in exports")


class AppConfig(BaseModel):
    """Configuración completa de la aplicación"""

    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)


def get_project_root() -> Path:
    """
    Obtiene la ruta raíz del proyecto (donde está el archivo README.md)

    Returns:
        Path: Ruta absoluta al directorio raíz del proyecto
    """
    current = Path(__file__).resolve()
    # Subir desde src/utils/ hasta la raíz (2 niveles)
    root = current.parent.parent.parent
    return root


def load_yaml_config(config_file: str = "ollama_config.yaml") -> Dict[str, Any]:
    """
    Carga configuración desde archivo YAML

    Args:
        config_file: Nombre del archivo de configuración (default: ollama_config.yaml)

    Returns:
        Dict con configuración cargada o diccionario vacío si falla
    """
    root = get_project_root()
    config_path = root / "config" / config_file

    if not config_path.exists():
        print(f"⚠️  Config file not found: {config_path}. Using defaults.")
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except Exception as e:
        print(f"⚠️  Error loading config from {config_path}: {e}. Using defaults.")
        return {}


def load_user_overrides() -> Dict[str, Any]:
    """
    Carga overrides de configuración del usuario desde user_overrides.yaml

    Este archivo permite al usuario sobrescribir configuración sin tocar
    el archivo principal ollama_config.yaml.

    Returns:
        Dict con overrides del usuario o diccionario vacío si no existen
    """
    root = get_project_root()
    overrides_path = root / "config" / "user_overrides.yaml"

    if not overrides_path.exists():
        return {}

    try:
        with open(overrides_path, "r", encoding="utf-8") as f:
            overrides = yaml.safe_load(f)
            return overrides if overrides else {}
    except Exception as e:
        print(f"⚠️  Error loading user overrides: {e}. Ignoring.")
        return {}


def save_user_overrides(overrides: Dict[str, Any]) -> bool:
    """
    Guarda overrides de configuración del usuario en user_overrides.yaml

    Args:
        overrides: Dict con configuración a guardar (estructura parcial de AppConfig)

    Returns:
        True si guardó exitosamente, False en caso de error

    Example:
        >>> save_user_overrides({
        ...     "ollama": {
        ...         "model": "llama3.2:3b",
        ...         "temperature": 0.3
        ...     }
        ... })
        True
    """
    root = get_project_root()
    config_dir = root / "config"
    overrides_path = config_dir / "user_overrides.yaml"

    # Crear directorio config si no existe
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(overrides_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(overrides, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ User overrides saved to {overrides_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving user overrides: {e}")
        return False


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge recursivo de dos diccionarios de configuración

    Args:
        base: Configuración base
        override: Overrides a aplicar sobre la base

    Returns:
        Dict con configuración merged
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def load_app_config() -> AppConfig:
    """
    Carga configuración completa de la aplicación desde:
    1. Valores por defecto (Pydantic defaults)
    2. Archivo YAML base (config/ollama_config.yaml)
    3. User overrides (config/user_overrides.yaml) - cambios de la UI
    4. Variables de entorno (OLLAMA_MODEL, OLLAMA_TEMPERATURE, etc.)

    Orden de precedencia: env vars > user overrides > YAML > defaults

    Returns:
        AppConfig: Configuración validada de la aplicación

    Example:
        >>> config = load_app_config()
        >>> print(config.ollama.model)
        'llama3.2:3b'
        >>> print(config.ocr.dpi)
        300
    """
    # 1. Cargar desde YAML base
    yaml_config = load_yaml_config("ollama_config.yaml")

    # 2. Cargar user overrides (cambios guardados desde UI)
    user_overrides = load_user_overrides()

    # 3. Merge YAML + user overrides
    merged_config = merge_configs(yaml_config, user_overrides)

    # 4. Override con variables de entorno si existen
    env_overrides = {}

    if os.getenv("OLLAMA_ENDPOINT"):
        env_overrides.setdefault("ollama", {})["endpoint"] = os.getenv("OLLAMA_ENDPOINT")

    if os.getenv("OLLAMA_MODEL"):
        env_overrides.setdefault("ollama", {})["model"] = os.getenv("OLLAMA_MODEL")

    if os.getenv("OLLAMA_TEMPERATURE"):
        env_overrides.setdefault("ollama", {})["temperature"] = float(os.getenv("OLLAMA_TEMPERATURE"))

    # Merge env overrides sobre configuración merged
    final_config = merge_configs(merged_config, env_overrides)

    # Validar con Pydantic
    try:
        config = AppConfig(**final_config)
        return config
    except Exception as e:
        print(f"⚠️  Error validating config: {e}. Using all defaults.")
        return AppConfig()


# Singleton global para evitar recargas
_app_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Obtiene configuración global de la aplicación (singleton)

    Returns:
        AppConfig: Configuración de la aplicación

    Example:
        >>> from src.utils.config_loader import get_config
        >>> config = get_config()
        >>> print(config.ollama.endpoint)
        'http://localhost:11434'
    """
    global _app_config
    if _app_config is None:
        _app_config = load_app_config()
    return _app_config


def reload_config() -> AppConfig:
    """
    Recarga configuración forzando nueva lectura de archivos y variables de entorno

    Returns:
        AppConfig: Nueva configuración cargada

    Example:
        >>> config = reload_config()  # Useful after editing config files
    """
    global _app_config
    _app_config = load_app_config()
    return _app_config


if __name__ == "__main__":
    # Test de carga de configuración
    print("=" * 60)
    print("Testing Configuration Loader")
    print("=" * 60)

    config = get_config()

    print("\n📋 Ollama Configuration:")
    print(f"  Endpoint: {config.ollama.endpoint}")
    print(f"  Model: {config.ollama.model}")
    print(f"  Temperature: {config.ollama.temperature}")
    print(f"  Max Tokens: {config.ollama.max_tokens}")

    print("\n📋 OCR Configuration:")
    print(f"  Enabled: {config.ocr.enabled}")
    print(f"  DPI: {config.ocr.dpi}")
    print(f"  Languages: {config.ocr.languages}")

    print("\n📋 Chunking Configuration:")
    print(f"  Enabled: {config.chunking.enabled}")
    print(f"  Max Chunk Size: {config.chunking.max_chunk_size}")

    print("\n📋 Export Configuration:")
    print(f"  Enabled: {config.export.enabled}")
    print(f"  Default Format: {config.export.default_format}")

    print("\n✅ Configuration loaded successfully!")
