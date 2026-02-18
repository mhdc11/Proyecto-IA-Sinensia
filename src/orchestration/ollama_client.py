"""
Ollama HTTP Client - Analizador de Documentos Legales

Cliente HTTP para comunicación con el servicio local de Ollama.
Maneja generación de texto, timeouts y errores de conexión.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import requests
from typing import Optional, Dict, Any
from pathlib import Path

from src.utils.config_loader import get_config


class OllamaClient:
    """
    Cliente HTTP para Ollama local

    Attributes:
        endpoint: URL del servicio Ollama (default: http://localhost:11434)
        timeout: Timeout en segundos para requests (default: 120)
    """

    def __init__(self, endpoint: Optional[str] = None, timeout: int = 120):
        """
        Inicializa el cliente Ollama

        Args:
            endpoint: URL de Ollama (None = cargar de config)
            timeout: Timeout en segundos para requests HTTP
        """
        config = get_config()
        self.endpoint = endpoint or config.ollama.endpoint
        self.timeout = timeout
        self.health_check_timeout = config.ollama.health_check_timeout

    def is_healthy(self) -> bool:
        """
        Verifica si Ollama está ejecutándose y accesible

        Returns:
            bool: True si Ollama responde correctamente

        Example:
            >>> client = OllamaClient()
            >>> if client.is_healthy():
            ...     print("Ollama is running")
        """
        try:
            response = requests.get(
                f"{self.endpoint}/api/version",
                timeout=self.health_check_timeout
            )
            return response.status_code == 200
        except Exception:
            return False

    def ollama_generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        stream: bool = False
    ) -> str:
        """
        Genera texto usando Ollama API

        Args:
            model: Nombre del modelo (ej: "llama3.2:3b")
            prompt: Prompt completo para el modelo
            temperature: Temperatura de generación (0.0-1.0)
            stream: Si True, streaming (no implementado en MVP)

        Returns:
            str: Texto generado por el modelo

        Raises:
            ConnectionError: Si Ollama no está accesible
            TimeoutError: Si la generación excede el timeout
            RuntimeError: Si Ollama retorna error

        Example:
            >>> client = OllamaClient()
            >>> response = client.ollama_generate(
            ...     model="llama3.2:3b",
            ...     prompt="¿Cuál es la capital de España?",
            ...     temperature=0.2
            ... )
            >>> print(response)
            'Madrid'
        """
        # Verificar que Ollama está ejecutándose
        if not self.is_healthy():
            raise ConnectionError(
                f"Ollama not running or not accessible at {self.endpoint}. "
                f"Start Ollama with: ollama serve"
            )

        # Preparar request body
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }

        try:
            print(f"🔄 Calling Ollama API (model={model}, temp={temperature})...")
            print(f"   Prompt length: {len(prompt)} characters")

            # Llamar a Ollama API
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=self.timeout
            )

            # Verificar status code
            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama API returned status {response.status_code}: "
                    f"{response.text}"
                )

            # Parsear respuesta JSON
            result = response.json()

            # Extraer texto generado
            generated_text = result.get("response", "")

            if not generated_text:
                raise RuntimeError("Ollama returned empty response")

            print(f"✅ Ollama generation complete: {len(generated_text)} characters")
            return generated_text

        except requests.Timeout as e:
            raise TimeoutError(
                f"Ollama request timed out after {self.timeout}s. "
                f"Document may be too large or Ollama is overloaded."
            ) from e
        except requests.ConnectionError as e:
            raise ConnectionError(
                f"Failed to connect to Ollama at {self.endpoint}: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}") from e

    def list_models(self) -> list[str]:
        """
        Lista los modelos disponibles en Ollama

        Returns:
            list[str]: Lista de nombres de modelos

        Example:
            >>> client = OllamaClient()
            >>> models = client.list_models()
            >>> print(models)
            ['llama3.2:3b', 'phi3:mini', 'mistral:7b']
        """
        try:
            response = requests.get(
                f"{self.endpoint}/api/tags",
                timeout=self.health_check_timeout
            )

            if response.status_code != 200:
                return []

            result = response.json()
            models = result.get("models", [])
            return [model["name"] for model in models]
        except Exception:
            return []


def ollama_generate(
    model: str,
    prompt: str,
    temperature: float = 0.2,
    endpoint: Optional[str] = None
) -> str:
    """
    Función standalone para generar texto con Ollama (API simplificada)

    Args:
        model: Nombre del modelo
        prompt: Prompt completo
        temperature: Temperatura (default: 0.2)
        endpoint: URL de Ollama (None = usar config)

    Returns:
        str: Texto generado

    Example:
        >>> from src.orchestration.ollama_client import ollama_generate
        >>> texto = ollama_generate("llama3.2:3b", "Hola, ¿cómo estás?")
    """
    client = OllamaClient(endpoint=endpoint)
    return client.ollama_generate(model, prompt, temperature)


if __name__ == "__main__":
    # Test del cliente Ollama
    print("=" * 60)
    print("Testing Ollama HTTP Client")
    print("=" * 60)

    # Crear cliente
    client = OllamaClient()

    print(f"\n📋 Ollama endpoint: {client.endpoint}")
    print(f"📋 Timeout: {client.timeout}s")

    # Test 1: Health check
    print("\n📋 Test 1: Health check")
    if client.is_healthy():
        print("✅ Ollama is running and accessible")
    else:
        print("❌ Ollama is not running. Start with: ollama serve")
        print("⚠️  Skipping remaining tests (Ollama not available)")
        exit(0)

    # Test 2: List models
    print("\n📋 Test 2: List available models")
    models = client.list_models()
    if models:
        print(f"✅ Available models ({len(models)}):")
        for model in models:
            print(f"   - {model}")
    else:
        print("⚠️  No models found. Pull a model with: ollama pull llama3.2:3b")

    # Test 3: Simple generation (solo si hay modelos)
    if models:
        print("\n📋 Test 3: Simple text generation")
        try:
            # Usar el primer modelo disponible
            test_model = models[0]
            test_prompt = "¿Cuál es la capital de España? Responde solo con el nombre de la ciudad."

            response = client.ollama_generate(
                model=test_model,
                prompt=test_prompt,
                temperature=0.1
            )

            print(f"✅ Generation successful!")
            print(f"   Model: {test_model}")
            print(f"   Prompt: {test_prompt}")
            print(f"   Response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Generation failed: {e}")

    # Test 4: Error handling (modelo inexistente)
    print("\n📋 Test 4: Error handling")
    try:
        client.ollama_generate("nonexistent-model", "test")
        print("❌ Should have raised RuntimeError")
    except RuntimeError as e:
        print(f"✅ Correctly raised RuntimeError: {str(e)[:100]}...")

    print("\n✅ Ollama client ready!")
    print("\n⚠️  Note: Ensure Ollama is running with: ollama serve")
    print("⚠️  Note: Pull a model with: ollama pull llama3.2:3b")
