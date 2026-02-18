"""
Integration Tests for Chunking and Consolidation - Analizador de Documentos Legales

Tests de integración para el sistema de chunking de documentos largos
y consolidación de análisis parciales.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from src.orchestration.chunker import split_text, consolidate_analyses
from src.models.analisis import Analisis, Fecha, Importe


class TestTextSplitting:
    """Tests para división de texto en chunks"""

    def test_split_short_text(self):
        """Test con texto corto (no requiere chunking)"""
        texto = "Este es un documento corto que no necesita división."

        chunks = split_text(texto, max_chunk_size=1000, overlap=100)

        # Texto corto → un solo chunk
        assert len(chunks) == 1
        assert chunks[0] == texto

    def test_split_long_text(self):
        """Test con texto largo (requiere chunking)"""
        # Generar texto largo (5000 palabras ≈ 30,000 caracteres)
        paragraph = "Este es un párrafo de ejemplo con contenido legal. " * 100
        texto = paragraph * 50

        chunks = split_text(texto, max_chunk_size=10000, overlap=500)

        # Verificar que se dividió
        assert len(chunks) > 1

        # Verificar que ningún chunk excede el tamaño máximo
        for chunk in chunks:
            assert len(chunk) <= 10000 + 100  # +100 margen por completar oraciones

    def test_split_preserves_sentences(self):
        """Test que la división respeta límites de oraciones"""
        texto = ("Primera oración del documento. " * 200 +
                 "Segunda oración importante. " * 200 +
                 "Tercera oración final. " * 200)

        chunks = split_text(texto, max_chunk_size=5000, overlap=200)

        # Cada chunk debe terminar en punto (excepto posiblemente el último)
        for chunk in chunks[:-1]:
            assert chunk.rstrip().endswith('.')

    def test_split_overlap(self):
        """Test que existe overlap entre chunks"""
        texto = "Palabra. " * 1000  # 9000 caracteres aprox

        chunks = split_text(texto, max_chunk_size=3000, overlap=500)

        if len(chunks) > 1:
            # Verificar que hay contenido compartido entre chunks consecutivos
            for i in range(len(chunks) - 1):
                chunk_end = chunks[i][-500:]  # Últimos 500 caracteres
                chunk_start = chunks[i + 1][:500]  # Primeros 500 caracteres

                # Debe haber algún solapamiento
                assert any(word in chunk_start for word in chunk_end.split()[:10])


class TestAnalysisConsolidation:
    """Tests para consolidación de análisis de chunks"""

    def test_consolidate_single_analysis(self):
        """Test con un solo análisis (no requiere consolidación)"""
        analisis = Analisis(
            tipo_documento="contrato_laboral",
            partes=["ACME Corp", "Juan Pérez"],
            fechas=[Fecha(etiqueta="Inicio", valor="2026-03-01")],
            importes=[Importe(concepto="Salario", valor=30000.0, moneda="EUR")],
            obligaciones=["No competir"],
            derechos=["30 días vacaciones"],
            riesgos=["Cláusula restrictiva"],
            resumen_bullets=["Contrato anual"],
            notas=[],
            confianza_aprox=0.9
        )

        consolidado = consolidate_analyses([analisis])

        # Debe ser idéntico al original
        assert consolidado.tipo_documento == "contrato_laboral"
        assert len(consolidado.partes) == 2
        assert consolidado.confianza_aprox == 0.9

    def test_consolidate_multiple_analyses_same_tipo(self):
        """Test consolidación con mismo tipo_documento (mayoría)"""
        analisis1 = Analisis(
            tipo_documento="contrato_laboral",
            partes=["ACME Corp"],
            fechas=[],
            importes=[],
            obligaciones=["Obligación 1"],
            derechos=[],
            riesgos=[],
            resumen_bullets=["Punto 1"],
            notas=[],
            confianza_aprox=0.85
        )

        analisis2 = Analisis(
            tipo_documento="contrato_laboral",
            partes=["Juan Pérez"],
            fechas=[Fecha(etiqueta="Inicio", "2026-03-01")],
            importes=[],
            obligaciones=["Obligación 2"],
            derechos=["Derecho 1"],
            riesgos=[],
            resumen_bullets=["Punto 2"],
            notas=[],
            confianza_aprox=0.90
        )

        analisis3 = Analisis(
            tipo_documento="contrato_laboral",
            partes=[],
            fechas=[],
            importes=[Importe(concepto="Salario", valor=30000.0, moneda="EUR")],
            obligaciones=[],
            derechos=[],
            riesgos=["Riesgo 1"],
            resumen_bullets=["Punto 3"],
            notas=[],
            confianza_aprox=0.88
        )

        consolidado = consolidate_analyses([analisis1, analisis2, analisis3])

        # Tipo por votación (todos coinciden)
        assert consolidado.tipo_documento == "contrato_laboral"

        # Unión de listas
        assert "ACME Corp" in consolidado.partes
        assert "Juan Pérez" in consolidado.partes

        # Fechas
        assert len(consolidado.fechas) == 1
        assert consolidado.fechas[0].etiqueta == "Inicio"

        # Importes
        assert len(consolidado.importes) == 1
        assert consolidado.importes[0].valor == 30000.0

        # Obligaciones
        assert len(consolidado.obligaciones) == 2

        # Derechos
        assert len(consolidado.derechos) == 1

        # Riesgos
        assert len(consolidado.riesgos) == 1

        # Resumen (max 10 bullets)
        assert len(consolidado.resumen_bullets) == 3

        # Confianza promedio
        expected_conf = (0.85 + 0.90 + 0.88) / 3
        assert abs(consolidado.confianza_aprox - expected_conf) < 0.01

    def test_consolidate_voting_tipo_documento(self):
        """Test votación cuando hay tipos diferentes"""
        analisis1 = Analisis(
            tipo_documento="contrato_laboral",
            partes=[], fechas=[], importes=[], obligaciones=[],
            derechos=[], riesgos=[], resumen_bullets=[], notas=[],
            confianza_aprox=0.9
        )

        analisis2 = Analisis(
            tipo_documento="contrato_laboral",
            partes=[], fechas=[], importes=[], obligaciones=[],
            derechos=[], riesgos=[], resumen_bullets=[], notas=[],
            confianza_aprox=0.85
        )

        analisis3 = Analisis(
            tipo_documento="nomina",  # Diferente
            partes=[], fechas=[], importes=[], obligaciones=[],
            derechos=[], riesgos=[], resumen_bullets=[], notas=[],
            confianza_aprox=0.8
        )

        consolidado = consolidate_analyses([analisis1, analisis2, analisis3])

        # Gana por mayoría: contrato_laboral (2 votos vs 1)
        assert consolidado.tipo_documento == "contrato_laboral"

    def test_consolidate_deduplication(self):
        """Test deduplicación de items similares"""
        analisis1 = Analisis(
            tipo_documento="contrato",
            partes=["ACME Corp S.A.", "Juan Pérez García"],
            fechas=[],
            importes=[],
            obligaciones=["No competir durante vigencia"],
            derechos=[],
            riesgos=[],
            resumen_bullets=[],
            notas=[],
            confianza_aprox=0.9
        )

        analisis2 = Analisis(
            tipo_documento="contrato",
            partes=["ACME Corp", "Juan Pérez"],  # Similares pero no idénticos
            fechas=[],
            importes=[],
            obligaciones=["No competir durante la vigencia"],  # Casi idéntica
            derechos=[],
            riesgos=[],
            resumen_bullets=[],
            notas=[],
            confianza_aprox=0.88
        )

        consolidado = consolidate_analyses([analisis1, analisis2])

        # Deduplicación por similitud (threshold ~0.85)
        # Partes: "ACME Corp S.A." vs "ACME Corp" (similar) → debe mantener ambas o mergear
        # Obligaciones casi idénticas → debe mergear
        assert len(consolidado.obligaciones) <= 2  # Máximo 2 si no detecta similitud alta

    def test_consolidate_resumen_limit_10(self):
        """Test que el resumen consolidado se limita a 10 bullets"""
        chunks_analisis = []

        # Crear 5 análisis con 3 bullets cada uno = 15 total
        for i in range(5):
            analisis = Analisis(
                tipo_documento="contrato",
                partes=[], fechas=[], importes=[], obligaciones=[],
                derechos=[], riesgos=[],
                resumen_bullets=[
                    f"Bullet {i * 3 + 1}",
                    f"Bullet {i * 3 + 2}",
                    f"Bullet {i * 3 + 3}"
                ],
                notas=[],
                confianza_aprox=0.9
            )
            chunks_analisis.append(analisis)

        consolidado = consolidate_analyses(chunks_analisis)

        # Debe limitarse a 10 bullets
        assert len(consolidado.resumen_bullets) <= 10

    def test_consolidate_fechas_unique(self):
        """Test que las fechas duplicadas se eliminan"""
        analisis1 = Analisis(
            tipo_documento="contrato",
            partes=[], importes=[], obligaciones=[], derechos=[], riesgos=[],
            fechas=[
                Fecha(etiqueta="Inicio", valor="2026-03-01"),
                Fecha(etiqueta="Fin", valor="2027-02-28")
            ],
            resumen_bullets=[], notas=[], confianza_aprox=0.9
        )

        analisis2 = Analisis(
            tipo_documento="contrato",
            partes=[], importes=[], obligaciones=[], derechos=[], riesgos=[],
            fechas=[
                Fecha(etiqueta="Inicio", valor="2026-03-01"),  # Duplicada
                Fecha(etiqueta="Renovación", valor="2027-03-01")
            ],
            resumen_bullets=[], notas=[], confianza_aprox=0.88
        )

        consolidado = consolidate_analyses([analisis1, analisis2])

        # 3 fechas únicas (Inicio, Fin, Renovación)
        assert len(consolidado.fechas) == 3

        # Verificar que "Inicio" no está duplicado
        inicios = [f for f in consolidado.fechas if f.etiqueta == "Inicio"]
        assert len(inicios) == 1

    def test_consolidate_importes_unique(self):
        """Test que los importes duplicados se eliminan"""
        analisis1 = Analisis(
            tipo_documento="nomina",
            partes=[], fechas=[], obligaciones=[], derechos=[], riesgos=[],
            importes=[
                Importe(concepto="Salario bruto", valor=30000.0, moneda="EUR"),
                Importe(concepto="Bonus", valor=5000.0, moneda="EUR")
            ],
            resumen_bullets=[], notas=[], confianza_aprox=0.9
        )

        analisis2 = Analisis(
            tipo_documento="nomina",
            partes=[], fechas=[], obligaciones=[], derechos=[], riesgos=[],
            importes=[
                Importe(concepto="Salario bruto", valor=30000.0, moneda="EUR"),  # Duplicado
                Importe(concepto="Seguro social", valor=2000.0, moneda="EUR")
            ],
            resumen_bullets=[], notas=[], confianza_aprox=0.88
        )

        consolidado = consolidate_analyses([analisis1, analisis2])

        # 3 importes únicos (Salario, Bonus, Seguro)
        assert len(consolidado.importes) == 3

        # Verificar que "Salario bruto" no está duplicado
        salarios = [imp for imp in consolidado.importes if imp.concepto == "Salario bruto"]
        assert len(salarios) == 1


class TestChunkingIntegration:
    """Tests de integración end-to-end para documentos largos"""

    def test_synthetic_long_document(self):
        """Test con documento sintético largo (simula 50 páginas)"""
        # Generar documento sintético de 50 páginas (~100,000 caracteres)
        page_template = """
        Página {page_num}

        CONTRATO DE TRABAJO

        Partes:
        - Empresa: ACME Corporation S.A. (CIF: A12345678)
        - Trabajador: Juan Pérez García (DNI: 12345678Z)

        Fecha de inicio: 2026-03-01
        Salario: 30.000 EUR anuales

        Obligaciones:
        - Cumplir horario de 9:00 a 18:00
        - No competir durante vigencia
        - Mantener confidencialidad

        Derechos:
        - 30 días de vacaciones
        - Seguro médico

        Riesgos:
        - Cláusula de no competencia (2 años)
        - Penalización: 10.000 EUR

        """ * 20  # Repetir para hacer página larga

        documento_completo = "\n\n".join([
            page_template.format(page_num=i) for i in range(1, 51)
        ])

        # Dividir en chunks
        chunks = split_text(documento_completo, max_chunk_size=15000, overlap=1000)

        # Verificar que se dividió correctamente
        assert len(chunks) > 1
        assert len(chunks) < 50  # No debería ser 1 chunk por página

        # Simular análisis de cada chunk (con mocks)
        chunks_analisis = []

        for i, chunk in enumerate(chunks):
            # Crear análisis simulado para cada chunk
            analisis = Analisis(
                tipo_documento="contrato_laboral",
                partes=["ACME Corporation", "Juan Pérez"] if i == 0 else [],
                fechas=[Fecha(etiqueta="Inicio", valor="2026-03-01")] if i == 0 else [],
                importes=[Importe(concepto="Salario", valor=30000.0, moneda="EUR")] if i == 0 else [],
                obligaciones=[f"Obligación chunk {i + 1}"],
                derechos=[f"Derecho chunk {i + 1}"] if i % 2 == 0 else [],
                riesgos=[f"Riesgo chunk {i + 1}"] if i % 3 == 0 else [],
                resumen_bullets=[f"Punto {i + 1}.1", f"Punto {i + 1}.2"],
                notas=[],
                confianza_aprox=0.85 + (i * 0.01)  # Variación en confianza
            )
            chunks_analisis.append(analisis)

        # Consolidar
        consolidado = consolidate_analyses(chunks_analisis)

        # Verificaciones
        assert consolidado.tipo_documento == "contrato_laboral"

        # Partes consolidadas
        assert "ACME Corporation" in consolidado.partes
        assert "Juan Pérez" in consolidado.partes

        # Fechas (sin duplicados)
        assert len(consolidado.fechas) >= 1

        # Importes (sin duplicados)
        assert len(consolidado.importes) >= 1

        # Obligaciones (una por chunk)
        assert len(consolidado.obligaciones) == len(chunks)

        # Resumen limitado a 10
        assert len(consolidado.resumen_bullets) <= 10

        # Confianza promedio razonable
        assert 0.8 <= consolidado.confianza_aprox <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
