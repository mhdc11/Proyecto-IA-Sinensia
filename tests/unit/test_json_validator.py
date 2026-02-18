"""
Unit Tests for JSON Parser/Validator - Analizador de Documentos Legales

Tests del parser de respuestas JSON del LLM, incluyendo casos con ruido,
JSON inválido, campos faltantes, y validación con Pydantic.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import pytest
import json
from pydantic import ValidationError

from src.models.analisis import Analisis, Fecha, Importe
from src.orchestration.prompt_builder import extract_json_from_response


class TestJSONExtraction:
    """Tests para extracción de JSON desde respuestas con ruido"""

    def test_extract_clean_json(self):
        """Test con JSON limpio sin ruido"""
        response = '''{
            "tipo_documento": "contrato",
            "partes": ["Empresa", "Trabajador"],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": ["Resumen"],
            "notas": [],
            "confianza_aprox": 0.9
        }'''

        extracted = extract_json_from_response(response)
        data = json.loads(extracted)

        assert data["tipo_documento"] == "contrato"
        assert len(data["partes"]) == 2

    def test_extract_json_with_prefix_text(self):
        """Test con texto antes del JSON"""
        response = '''Aquí está el análisis del documento:

        {
            "tipo_documento": "nomina",
            "partes": ["Empresa"],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": ["Pago mensual"],
            "notas": [],
            "confianza_aprox": 0.85
        }'''

        extracted = extract_json_from_response(response)
        data = json.loads(extracted)

        assert data["tipo_documento"] == "nomina"

    def test_extract_json_with_suffix_text(self):
        """Test con texto después del JSON"""
        response = '''{
            "tipo_documento": "convenio",
            "partes": [],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": [],
            "notas": [],
            "confianza_aprox": 0.8
        }

        Espero que este análisis sea útil.'''

        extracted = extract_json_from_response(response)
        data = json.loads(extracted)

        assert data["tipo_documento"] == "convenio"

    def test_extract_json_with_both_sides_noise(self):
        """Test con ruido antes y después del JSON"""
        response = '''El documento ha sido analizado exitosamente.

        A continuación el resultado en formato JSON:

        {
            "tipo_documento": "contrato_laboral",
            "partes": ["ACME Corp", "Juan Pérez"],
            "fechas": [{"etiqueta": "Inicio", "valor": "2026-03-01"}],
            "importes": [{"concepto": "Salario", "valor": 30000.0, "moneda": "EUR"}],
            "obligaciones": ["No competir"],
            "derechos": ["Vacaciones"],
            "riesgos": ["Cláusula restrictiva"],
            "resumen_bullets": ["Contrato anual"],
            "notas": ["Documento legible"],
            "confianza_aprox": 0.92
        }

        El análisis se completó con éxito. Si necesitas más información, avísame.'''

        extracted = extract_json_from_response(response)
        data = json.loads(extracted)

        assert data["tipo_documento"] == "contrato_laboral"
        assert len(data["partes"]) == 2
        assert data["confianza_aprox"] == 0.92

    def test_extract_json_with_markdown_code_block(self):
        """Test con JSON dentro de bloque de código markdown"""
        response = '''```json
        {
            "tipo_documento": "poder",
            "partes": ["Poderdante", "Apoderado"],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": ["Poder notarial"],
            "notas": [],
            "confianza_aprox": 0.75
        }
        ```'''

        extracted = extract_json_from_response(response)
        data = json.loads(extracted)

        assert data["tipo_documento"] == "poder"

    def test_extract_json_nested_braces(self):
        """Test con llaves anidadas en strings"""
        response = '''{
            "tipo_documento": "contrato",
            "partes": ["Empresa {con paréntesis}"],
            "fechas": [],
            "importes": [],
            "obligaciones": ["Cumplir {obligación especial}"],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": ["Contrato con {cláusula especial}"],
            "notas": [],
            "confianza_aprox": 0.88
        }'''

        extracted = extract_json_from_response(response)
        data = json.loads(extracted)

        assert "{con paréntesis}" in data["partes"][0]
        assert "{obligación especial}" in data["obligaciones"][0]

    def test_extract_invalid_json(self):
        """Test con JSON inválido (sin llaves de cierre)"""
        response = '''{
            "tipo_documento": "contrato",
            "partes": ["Empresa"]
            # Falta cierre de llave'''

        with pytest.raises((json.JSONDecodeError, ValueError)):
            extracted = extract_json_from_response(response)
            json.loads(extracted)

    def test_extract_no_json(self):
        """Test con respuesta sin JSON"""
        response = "Lo siento, no pude analizar el documento. Es demasiado corto."

        with pytest.raises((json.JSONDecodeError, ValueError)):
            extracted = extract_json_from_response(response)
            json.loads(extracted)


class TestPydanticValidation:
    """Tests de validación con modelos Pydantic"""

    def test_valid_analisis(self):
        """Test con análisis válido completo"""
        data = {
            "tipo_documento": "contrato_laboral",
            "partes": ["ACME Corp", "Juan Pérez"],
            "fechas": [{"etiqueta": "Inicio", "valor": "2026-03-01"}],
            "importes": [{"concepto": "Salario", "valor": 30000.0, "moneda": "EUR"}],
            "obligaciones": ["No competir"],
            "derechos": ["30 días vacaciones"],
            "riesgos": ["Cláusula no competencia"],
            "resumen_bullets": ["Contrato de 1 año"],
            "notas": ["Buena calidad"],
            "confianza_aprox": 0.9
        }

        analisis = Analisis(**data)

        assert analisis.tipo_documento == "contrato_laboral"
        assert len(analisis.partes) == 2
        assert analisis.confianza_aprox == 0.9

    def test_valid_analisis_minimal(self):
        """Test con campos mínimos (listas vacías)"""
        data = {
            "tipo_documento": "desconocido",
            "partes": [],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": [],
            "notas": [],
            "confianza_aprox": 0.5
        }

        analisis = Analisis(**data)

        assert analisis.tipo_documento == "desconocido"
        assert len(analisis.partes) == 0

    def test_missing_required_field(self):
        """Test con campo requerido faltante"""
        data = {
            "tipo_documento": "contrato",
            # Falta "partes" y otros campos requeridos
            "confianza_aprox": 0.8
        }

        with pytest.raises(ValidationError) as exc_info:
            Analisis(**data)

        # Verificar que menciona campos faltantes
        errors = exc_info.value.errors()
        missing_fields = [e['loc'][0] for e in errors if e['type'] == 'missing']
        assert 'partes' in missing_fields

    def test_invalid_field_type(self):
        """Test con tipo de campo inválido"""
        data = {
            "tipo_documento": "contrato",
            "partes": ["Empresa"],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": [],
            "notas": [],
            "confianza_aprox": "noventa"  # Debe ser float
        }

        with pytest.raises(ValidationError):
            Analisis(**data)

    def test_confianza_out_of_range(self):
        """Test con confianza fuera de rango 0-1"""
        data = {
            "tipo_documento": "contrato",
            "partes": [],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": [],
            "notas": [],
            "confianza_aprox": 1.5  # > 1.0
        }

        with pytest.raises(ValidationError):
            Analisis(**data)

    def test_fecha_structure(self):
        """Test estructura de Fecha"""
        fecha = Fecha(etiqueta="Inicio", valor="2026-03-01")

        assert fecha.etiqueta == "Inicio"
        assert fecha.valor == "2026-03-01"

    def test_fecha_invalid(self):
        """Test Fecha con campos faltantes"""
        with pytest.raises(ValidationError):
            Fecha(etiqueta="Inicio")  # Falta valor

    def test_importe_structure(self):
        """Test estructura de Importe"""
        importe = Importe(
            concepto="Salario bruto",
            valor=35000.0,
            moneda="EUR"
        )

        assert importe.concepto == "Salario bruto"
        assert importe.valor == 35000.0
        assert importe.moneda == "EUR"

    def test_importe_optional_fields(self):
        """Test Importe con campos opcionales None"""
        importe = Importe(
            concepto="Importe sin especificar",
            valor=None,
            moneda=None
        )

        assert importe.concepto == "Importe sin especificar"
        assert importe.valor is None
        assert importe.moneda is None


class TestJSONWithSpecialCharacters:
    """Tests con caracteres especiales UTF-8"""

    def test_spanish_characters(self):
        """Test con caracteres españoles (ñ, á, é, etc.)"""
        data = {
            "tipo_documento": "contrato",
            "partes": ["Empresa Española S.A.", "José María García"],
            "fechas": [],
            "importes": [{"concepto": "Indemnización", "valor": 5000.0, "moneda": "€"}],
            "obligaciones": ["Cumplir según normativa española"],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": ["Contrato español"],
            "notas": [],
            "confianza_aprox": 0.9
        }

        analisis = Analisis(**data)

        assert "Española" in analisis.partes[0]
        assert "José María" in analisis.partes[1]
        assert analisis.importes[0].moneda == "€"

    def test_quotes_in_strings(self):
        """Test con comillas dentro de strings"""
        data = {
            "tipo_documento": "contrato",
            "partes": ['Empresa "La Innovadora" S.A.'],
            "fechas": [],
            "importes": [],
            "obligaciones": ["Cumplir 'estrictamente' el horario"],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": [],
            "notas": [],
            "confianza_aprox": 0.85
        }

        analisis = Analisis(**data)

        assert '"La Innovadora"' in analisis.partes[0]
        assert "'estrictamente'" in analisis.obligaciones[0]


class TestJSONRecovery:
    """Tests de recuperación ante errores"""

    def test_partial_json_recovery(self):
        """Test con JSON parcialmente corrupto"""
        # JSON con campo extra no reconocido (debería ignorarlo)
        data = {
            "tipo_documento": "contrato",
            "partes": ["Empresa"],
            "fechas": [],
            "importes": [],
            "obligaciones": [],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": [],
            "notas": [],
            "confianza_aprox": 0.8,
            "campo_extra_desconocido": "valor"  # Campo no esperado
        }

        # Pydantic ignora campos extra por defecto
        analisis = Analisis(**data)

        assert analisis.tipo_documento == "contrato"
        # campo_extra_desconocido se ignora

    def test_empty_strings_in_lists(self):
        """Test con strings vacíos en listas (deberían filtrarse)"""
        data = {
            "tipo_documento": "contrato",
            "partes": ["Empresa", "", "Trabajador", ""],
            "fechas": [],
            "importes": [],
            "obligaciones": ["Obligación 1", "", "Obligación 2"],
            "derechos": [],
            "riesgos": [],
            "resumen_bullets": [],
            "notas": [],
            "confianza_aprox": 0.85
        }

        analisis = Analisis(**data)

        # Pydantic permite strings vacíos, pero el código puede filtrarlos
        assert len(analisis.partes) == 4  # Incluye vacíos (filtrado en postproceso)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
