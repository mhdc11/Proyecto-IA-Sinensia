"""
Privacy Compliance Validation - Analizador de Documentos Legales

Script que revisa el código fuente para garantizar cumplimiento con el
principio constitucional de privacidad: no realizar llamadas a servicios
externos excepto localhost:11434 (Ollama local).

Usage:
    python tests/privacy_compliance_check.py [--verbose]

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict


class PrivacyComplianceChecker:
    """
    Valida que el código cumple con el principio de privacidad
    verificando que no existan llamadas a servicios externos
    """

    # Patrones sospechosos de llamadas externas
    SUSPICIOUS_PATTERNS = [
        # URLs remotas
        (r'https?://(?!localhost|127\.0\.0\.1)', 'URL remota detectada'),
        # Dominio explícito que no sea localhost
        (r'\.com|\.net|\.org|\.io|\.ai|\.dev', 'Dominio externo detectado'),
        # APIs conocidas de servicios externos
        (r'openai|anthropic|cohere|huggingface|replicate', 'API de servicio externo detectada (posible)'),
        # Envío de datos (requests, urllib, aiohttp)
        (r'requests\.(post|put|patch)\s*\(', 'POST/PUT/PATCH request detectado'),
    ]

    # Patrones permitidos (whitelist)
    ALLOWED_PATTERNS = [
        r'localhost:11434',  # Ollama local
        r'127\.0\.0\.1:11434',  # Ollama local (IP)
        r'http://localhost',  # Localhost genérico
        r'http://127\.0\.0\.1',  # IP local
    ]

    def __init__(self, src_dir: Path, verbose: bool = False):
        self.src_dir = src_dir
        self.verbose = verbose
        self.violations: List[Dict] = []

    def log(self, message: str):
        """Log condicional según verbose"""
        if self.verbose:
            print(f"[PRIVACY] {message}")

    def is_allowed(self, line: str) -> bool:
        """
        Verifica si una línea contiene un patrón permitido

        Returns:
            True si la línea es segura (contiene patrón permitido)
        """
        for pattern in self.ALLOWED_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def scan_file(self, file_path: Path) -> List[Dict]:
        """
        Escanea un archivo Python en busca de violaciones de privacidad

        Returns:
            Lista de diccionarios con violaciones encontradas
        """
        violations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Saltar comentarios y líneas vacías
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue

                # Verificar si está en whitelist primero
                if self.is_allowed(line):
                    continue

                # Buscar patrones sospechosos
                for pattern, description in self.SUSPICIOUS_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append({
                            'file': str(file_path.relative_to(self.src_dir.parent)),
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern,
                            'description': description
                        })

        except Exception as e:
            self.log(f"Error leyendo {file_path}: {e}")

        return violations

    def scan_directory(self) -> Dict[str, List[Dict]]:
        """
        Escanea recursivamente el directorio src/ en busca de violaciones

        Returns:
            Dict mapeando archivos a listas de violaciones
        """
        self.log(f"Escaneando: {self.src_dir}")

        violations_by_file = defaultdict(list)

        # Buscar todos los archivos .py en src/
        for py_file in self.src_dir.rglob("*.py"):
            # Saltar __pycache__ y tests
            if '__pycache__' in str(py_file) or 'test_' in py_file.name:
                continue

            self.log(f"  Revisando: {py_file.relative_to(self.src_dir.parent)}")

            violations = self.scan_file(py_file)

            if violations:
                violations_by_file[str(py_file.relative_to(self.src_dir.parent))].extend(violations)

        return dict(violations_by_file)

    def print_report(self, violations_by_file: Dict[str, List[Dict]]):
        """
        Imprime reporte de compliance en consola

        Args:
            violations_by_file: Dict con violaciones por archivo
        """
        print("\n" + "=" * 70)
        print("REPORTE DE CUMPLIMIENTO DE PRIVACIDAD")
        print("=" * 70)

        if not violations_by_file:
            print("✅ **CUMPLIMIENTO VERIFICADO**")
            print("\nNo se detectaron llamadas a servicios externos no autorizados.")
            print("El sistema cumple con el principio constitucional de privacidad.")
            print("\nServicios permitidos:")
            print("  - Ollama local (localhost:11434 / 127.0.0.1:11434)")
            print("=" * 70 + "\n")
            return

        # Hay violaciones
        total_violations = sum(len(v) for v in violations_by_file.values())

        print(f"⚠️  **{total_violations} POSIBLE(S) VIOLACIÓN(ES) DETECTADA(S)**\n")

        for file_path, violations in violations_by_file.items():
            print(f"📄 {file_path}")

            for violation in violations:
                print(f"   Línea {violation['line']}: {violation['description']}")
                print(f"   └─ {violation['content'][:80]}")
                print()

        print("=" * 70)
        print("\n⚠️  IMPORTANTE:")
        print("   Revisa manualmente cada violación detectada.")
        print("   Si son falsos positivos (ej: comentarios, tests), ignóralos.")
        print("   Si son reales, ELIMINA las llamadas externas para cumplir la constitución.")
        print("=" * 70 + "\n")

    def validate(self) -> bool:
        """
        Ejecuta validación completa

        Returns:
            True si cumple (sin violaciones), False si hay violaciones
        """
        violations_by_file = self.scan_directory()
        self.print_report(violations_by_file)

        return len(violations_by_file) == 0


def main():
    """Punto de entrada del script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validador de cumplimiento de privacidad"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar salida detallada"
    )
    parser.add_argument(
        "--src-dir",
        type=str,
        default="src",
        help="Directorio de código fuente (default: src)"
    )

    args = parser.parse_args()

    # Obtener directorio del proyecto
    project_root = Path(__file__).parent.parent
    src_dir = project_root / args.src_dir

    if not src_dir.exists():
        print(f"❌ Error: Directorio src/ no existe: {src_dir}")
        return 1

    # Ejecutar validación
    checker = PrivacyComplianceChecker(src_dir, verbose=args.verbose)
    compliant = checker.validate()

    # Exit code: 0 si cumple, 1 si hay violaciones
    return 0 if compliant else 1


if __name__ == "__main__":
    sys.exit(main())
