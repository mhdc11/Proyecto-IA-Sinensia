"""
Performance Benchmark - Analizador de Documentos Legales

Script para medir tiempos de extracción, OCR, LLM y análisis total
en documentos típicos (5-10 páginas PDF nativo, 5 páginas escaneado).

Usage:
    python tests/performance/benchmark.py [--verbose] [--output results.json]

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import time
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from statistics import mean, stdev

# Añadir src/ al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.pdf_native import extract_pdf_native
from src.extraction.pdf_ocr import extract_pdf_ocr
from src.extraction.docx_extractor import extract_docx
from src.extraction.auto_extractor import extract_text_auto
from src.orchestration.analyzer import analyze_document
from src.utils.logging_config import Timer


class PerformanceBenchmark:
    """
    Framework de benchmarking para medir rendimiento del sistema
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []

    def log(self, message: str):
        """Log condicional según verbose"""
        if self.verbose:
            print(f"[BENCHMARK] {message}")

    def measure_extraction_native(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Mide tiempo de extracción de PDF nativo

        Returns:
            Dict con tiempo_segundos, paginas, caracteres
        """
        self.log(f"Midiendo extracción nativa: {pdf_path.name}")

        timer = Timer()
        timer.start()

        try:
            texto, paginas = extract_pdf_native(pdf_path)
            tiempo = timer.stop()

            return {
                "tipo": "extraccion_nativa",
                "archivo": pdf_path.name,
                "tiempo_segundos": tiempo,
                "paginas": paginas,
                "caracteres": len(texto),
                "exito": True
            }

        except Exception as e:
            tiempo = timer.stop()
            return {
                "tipo": "extraccion_nativa",
                "archivo": pdf_path.name,
                "tiempo_segundos": tiempo,
                "exito": False,
                "error": str(e)
            }

    def measure_extraction_ocr(self, pdf_path: Path, dpi: int = 300, lang: str = "spa") -> Dict[str, Any]:
        """
        Mide tiempo de extracción con OCR

        Returns:
            Dict con tiempo_segundos, paginas, caracteres
        """
        self.log(f"Midiendo OCR: {pdf_path.name} (DPI={dpi}, lang={lang})")

        timer = Timer()
        timer.start()

        try:
            texto, paginas = extract_pdf_ocr(pdf_path, dpi=dpi, lang=lang)
            tiempo = timer.stop()

            return {
                "tipo": "extraccion_ocr",
                "archivo": pdf_path.name,
                "tiempo_segundos": tiempo,
                "paginas": paginas,
                "caracteres": len(texto),
                "dpi": dpi,
                "idioma": lang,
                "exito": True
            }

        except Exception as e:
            tiempo = timer.stop()
            return {
                "tipo": "extraccion_ocr",
                "archivo": pdf_path.name,
                "tiempo_segundos": tiempo,
                "exito": False,
                "error": str(e)
            }

    def measure_full_analysis(self, file_path: Path) -> Dict[str, Any]:
        """
        Mide tiempo del análisis completo end-to-end

        Returns:
            Dict con tiempos desglosados y total
        """
        self.log(f"Midiendo análisis completo: {file_path.name}")

        timer_total = Timer()
        timer_total.start()

        try:
            documento, analisis, dupla = analyze_document(file_path)
            tiempo_total = timer_total.stop()

            return {
                "tipo": "analisis_completo",
                "archivo": file_path.name,
                "tiempo_total_segundos": tiempo_total,
                "tipo_documento": analisis.tipo_documento,
                "paginas": documento.paginas,
                "tipo_fuente": documento.tipo_fuente.value,
                "categorias_no_vacias": sum([
                    len(analisis.partes) > 0,
                    len(analisis.fechas) > 0,
                    len(analisis.importes) > 0,
                    len(analisis.obligaciones) > 0,
                    len(analisis.derechos) > 0,
                    len(analisis.riesgos) > 0,
                    len(analisis.resumen_bullets) > 0
                ]),
                "confianza": analisis.confianza_aprox,
                "exito": True
            }

        except Exception as e:
            tiempo_total = timer_total.stop()
            return {
                "tipo": "analisis_completo",
                "archivo": file_path.name,
                "tiempo_total_segundos": tiempo_total,
                "exito": False,
                "error": str(e)
            }

    def run_benchmark_suite(self, test_files: List[Path]) -> Dict[str, Any]:
        """
        Ejecuta suite completa de benchmarks

        Args:
            test_files: Lista de archivos a probar

        Returns:
            Dict con resultados agregados y estadísticas
        """
        self.log("=" * 60)
        self.log("Iniciando Performance Benchmark Suite")
        self.log("=" * 60)

        suite_results = {
            "timestamp": datetime.now().isoformat(),
            "total_archivos": len(test_files),
            "resultados_individuales": [],
            "estadisticas": {}
        }

        # Ejecutar benchmarks para cada archivo
        for file_path in test_files:
            self.log(f"\n--- Procesando: {file_path.name} ---")

            # Análisis completo
            result = self.measure_full_analysis(file_path)
            suite_results["resultados_individuales"].append(result)

        # Calcular estadísticas agregadas
        suite_results["estadisticas"] = self._calculate_statistics(
            suite_results["resultados_individuales"]
        )

        return suite_results

    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estadísticas agregadas de los resultados

        Returns:
            Dict con promedios, desviaciones, mínimos, máximos
        """
        # Filtrar solo resultados exitosos
        successful = [r for r in results if r.get("exito", False)]

        if not successful:
            return {"error": "No hay resultados exitosos para calcular estadísticas"}

        # Extraer tiempos
        tiempos_totales = [r["tiempo_total_segundos"] for r in successful]

        stats = {
            "archivos_exitosos": len(successful),
            "archivos_fallidos": len(results) - len(successful),
            "tiempo_promedio_segundos": mean(tiempos_totales),
            "tiempo_min_segundos": min(tiempos_totales),
            "tiempo_max_segundos": max(tiempos_totales),
        }

        # Desviación estándar (solo si hay múltiples muestras)
        if len(tiempos_totales) > 1:
            stats["tiempo_stdev_segundos"] = stdev(tiempos_totales)

        # Promedio de confianza
        confianzas = [r.get("confianza", 0) for r in successful if "confianza" in r]
        if confianzas:
            stats["confianza_promedio"] = mean(confianzas)

        return stats

    def save_results(self, results: Dict[str, Any], output_path: Path):
        """
        Guarda resultados en archivo JSON

        Args:
            results: Diccionario de resultados
            output_path: Ruta al archivo de salida
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self.log(f"Resultados guardados en: {output_path}")

    def print_summary(self, results: Dict[str, Any]):
        """
        Imprime resumen de resultados en consola

        Args:
            results: Diccionario de resultados
        """
        print("\n" + "=" * 60)
        print("RESUMEN DE PERFORMANCE")
        print("=" * 60)

        stats = results.get("estadisticas", {})

        if "error" in stats:
            print(f"❌ {stats['error']}")
            return

        print(f"📊 Archivos procesados: {results['total_archivos']}")
        print(f"   ✅ Exitosos: {stats.get('archivos_exitosos', 0)}")
        print(f"   ❌ Fallidos: {stats.get('archivos_fallidos', 0)}")

        print(f"\n⏱️  Tiempos de Análisis:")
        print(f"   Promedio: {stats.get('tiempo_promedio_segundos', 0):.2f} s")
        print(f"   Mínimo:   {stats.get('tiempo_min_segundos', 0):.2f} s")
        print(f"   Máximo:   {stats.get('tiempo_max_segundos', 0):.2f} s")

        if 'tiempo_stdev_segundos' in stats:
            print(f"   Desv. Est: {stats['tiempo_stdev_segundos']:.2f} s")

        if 'confianza_promedio' in stats:
            print(f"\n🎯 Confianza Promedio: {stats['confianza_promedio']:.1%}")

        print("\n📝 Resultados Individuales:")
        for i, resultado in enumerate(results['resultados_individuales'], 1):
            estado = "✅" if resultado.get("exito", False) else "❌"
            nombre = resultado.get("archivo", "?")
            tiempo = resultado.get("tiempo_total_segundos", 0)
            print(f"   {i}. {estado} {nombre}: {tiempo:.2f} s")

        print("=" * 60 + "\n")


def main():
    """Punto de entrada del script de benchmarking"""
    parser = argparse.ArgumentParser(
        description="Benchmark de rendimiento del Analizador de Documentos"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar salida detallada"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="benchmark_results.json",
        help="Archivo de salida para resultados (default: benchmark_results.json)"
    )
    parser.add_argument(
        "--test-dir",
        type=str,
        default="tests/fixtures",
        help="Directorio con archivos de test"
    )

    args = parser.parse_args()

    # Inicializar benchmark
    benchmark = PerformanceBenchmark(verbose=args.verbose)

    # Buscar archivos de test
    test_dir = Path(args.test_dir)

    if not test_dir.exists():
        print(f"❌ Error: Directorio de test no existe: {test_dir}")
        print(f"\nPara ejecutar benchmarks, crea archivos de ejemplo en: {test_dir}/")
        print("  - Sugerencia: PDFs de 5-10 páginas con contenido legal")
        return

    # Recopilar archivos soportados
    test_files = []
    for ext in ['.pdf', '.docx', '.jpg', '.png']:
        test_files.extend(test_dir.glob(f"*{ext}"))

    if not test_files:
        print(f"❌ No se encontraron archivos de test en: {test_dir}")
        print("   Formatos soportados: .pdf, .docx, .jpg, .png")
        return

    print(f"📂 Archivos de test encontrados: {len(test_files)}")

    # Ejecutar suite de benchmarks
    results = benchmark.run_benchmark_suite(test_files)

    # Guardar resultados
    output_path = Path(args.output)
    benchmark.save_results(results, output_path)

    # Mostrar resumen
    benchmark.print_summary(results)


if __name__ == "__main__":
    main()
