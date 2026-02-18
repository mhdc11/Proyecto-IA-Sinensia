"""
Pytest Configuration - Analizador de Documentos Legales

Configuración global de pytest y fixtures compartidos.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import pytest
import sys
from pathlib import Path

# Añadir src/ al PYTHONPATH para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def fixtures_dir():
    """Ruta al directorio de fixtures"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_text_path(fixtures_dir):
    """Ruta al archivo de texto de ejemplo"""
    return fixtures_dir / "sample.txt"


@pytest.fixture
def mock_ollama_response():
    """Mock de respuesta de Ollama con JSON válido"""
    return {
        "model": "llama3.2:3b",
        "response": '''{
            "tipo_documento": "contrato_laboral",
            "partes": ["ACME Corp", "Juan Pérez"],
            "fechas": [{"etiqueta": "Inicio", "valor": "2026-03-01"}],
            "importes": [{"concepto": "Salario", "valor": 30000.0, "moneda": "EUR"}],
            "obligaciones": ["No competir"],
            "derechos": ["30 días vacaciones"],
            "riesgos": ["Cláusula no competencia"],
            "resumen_bullets": ["Contrato 1 año"],
            "notas": [],
            "confianza_aprox": 0.9
        }'''
    }


@pytest.fixture
def sample_dupla_dict():
    """Diccionario de ejemplo de una dupla completa"""
    return {
        "id": "abc123456789abcd",
        "documento": {
            "id": "abc123456789abcd",
            "nombre": "contrato_test.pdf",
            "tipo_fuente": "pdf_native",
            "paginas": 5,
            "bytes": 100000,
            "idioma_detectado": "es",
            "ts_ingesta": "2026-02-18T10:00:00"
        },
        "analisis": {
            "tipo_documento": "contrato_laboral",
            "partes": ["ACME Corp", "Juan Pérez"],
            "fechas": [{"etiqueta": "Inicio", "valor": "2026-03-01"}],
            "importes": [{"concepto": "Salario", "valor": 30000.0, "moneda": "EUR"}],
            "obligaciones": ["No competir"],
            "derechos": ["30 días vacaciones"],
            "riesgos": ["Cláusula restrictiva"],
            "resumen_bullets": ["Contrato anual"],
            "notas": [],
            "confianza_aprox": 0.9
        },
        "ts_creacion": "2026-02-18T10:00:00",
        "ts_actualizacion": "2026-02-18T10:00:00",
        "estado": "valido"
    }
