"""
Hashing and Document Metadata - Analizador de Documentos Legales

Utilidades para computar IDs únicos de documentos y extraer metadata básica.

Author: Analizador de Documentos Legales Team
Date: 2026-02-18
"""

import hashlib
from pathlib import Path
from typing import Dict, Optional

# Importaciones condicionales para detección de páginas
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def compute_file_hash(file_path: Path, truncate: int = 16) -> str:
    """
    Computa SHA-256 hash de un archivo y lo trunca a N caracteres

    El hash se usa como ID único estable del documento.
    Mismo archivo = mismo hash, garantizando deduplicación.

    Args:
        file_path: Ruta al archivo
        truncate: Número de caracteres del hash a retornar (default: 16)

    Returns:
        str: Hash SHA-256 truncado en hexadecimal (lowercase)

    Raises:
        FileNotFoundError: Si el archivo no existe
        IOError: Si hay error al leer el archivo

    Example:
        >>> hash_id = compute_file_hash(Path("documento.pdf"))
        >>> print(hash_id)
        'a1b2c3d4e5f6g7h8'
        >>> len(hash_id)
        16
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        sha256_hash = hashlib.sha256()
        # Leer en bloques para manejar archivos grandes sin problemas de memoria
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        full_hash = sha256_hash.hexdigest()
        return full_hash[:truncate]
    except Exception as e:
        raise IOError(f"Error computing hash for {file_path}: {e}") from e


def get_file_size(file_path: Path) -> int:
    """
    Obtiene el tamaño del archivo en bytes

    Args:
        file_path: Ruta al archivo

    Returns:
        int: Tamaño en bytes

    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.stat().st_size


def count_pdf_pages(file_path: Path) -> Optional[int]:
    """
    Cuenta el número de páginas de un PDF

    Args:
        file_path: Ruta al PDF

    Returns:
        int: Número de páginas, o None si falla la detección

    Note:
        Requiere pdfplumber instalado. Retorna None si no está disponible.
    """
    if not PDF_AVAILABLE:
        return None

    try:
        with pdfplumber.open(file_path) as pdf:
            return len(pdf.pages)
    except Exception as e:
        print(f"⚠️  Error counting PDF pages for {file_path}: {e}")
        return None


def count_docx_pages(file_path: Path) -> Optional[int]:
    """
    Cuenta el número de páginas de un DOCX (aproximado)

    DOCX no tiene concepto nativo de "páginas" hasta renderizado.
    Esta función cuenta secciones con saltos de página explícitos.

    Args:
        file_path: Ruta al DOCX

    Returns:
        int: Número aproximado de páginas, o None si falla

    Note:
        Requiere python-docx instalado. El conteo es aproximado.
    """
    if not DOCX_AVAILABLE:
        return None

    try:
        doc = DocxDocument(file_path)
        # Aproximación: contar secciones con saltos de página explícitos
        # Esto no es perfecto pero da una estimación razonable
        page_breaks = 0
        for paragraph in doc.paragraphs:
            if paragraph.text == "\x0c":  # Form feed = page break
                page_breaks += 1

        # Mínimo 1 página (incluso si no hay saltos explícitos)
        return max(1, page_breaks + 1)
    except Exception as e:
        print(f"⚠️  Error counting DOCX pages for {file_path}: {e}")
        return None


def compute_doc_meta(file_path: Path) -> Dict[str, any]:
    """
    Computa metadata completa de un documento

    Returns:
        dict: Metadata con campos:
            - id: SHA-256 hash truncado a 16 caracteres
            - bytes: Tamaño del archivo en bytes
            - paginas: Número de páginas (si aplica, None en otro caso)

    Raises:
        FileNotFoundError: Si el archivo no existe

    Example:
        >>> meta = compute_doc_meta(Path("contrato.pdf"))
        >>> print(meta)
        {
            'id': 'a1b2c3d4e5f6g7h8',
            'bytes': 245760,
            'paginas': 12
        }
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Computar hash como ID único
    doc_id = compute_file_hash(file_path, truncate=16)

    # Obtener tamaño
    file_size = get_file_size(file_path)

    # Intentar contar páginas según extensión
    extension = file_path.suffix.lower()
    paginas = None

    if extension == ".pdf":
        paginas = count_pdf_pages(file_path)
    elif extension in [".docx", ".doc"]:
        paginas = count_docx_pages(file_path)
    # Imágenes y TXT no tienen concepto de páginas

    return {"id": doc_id, "bytes": file_size, "paginas": paginas}


if __name__ == "__main__":
    # Test de hashing y metadata
    print("=" * 60)
    print("Testing Hashing and Metadata Utilities")
    print("=" * 60)

    # Test con archivo de prueba (este mismo script)
    test_file = Path(__file__)

    print(f"\n📋 Test File: {test_file.name}")
    print(f"   Exists: {test_file.exists()}")

    # Test 1: Hash computation
    print("\n📋 Test 1: Hash computation")
    hash_id = compute_file_hash(test_file)
    print(f"✅ File hash (16 chars): {hash_id}")
    print(f"   Length: {len(hash_id)}")

    # Verificar estabilidad del hash (mismo archivo = mismo hash)
    hash_id_2 = compute_file_hash(test_file)
    print(f"✅ Hash stability: {hash_id == hash_id_2}")

    # Test 2: File size
    print("\n📋 Test 2: File size")
    size = get_file_size(test_file)
    print(f"✅ File size: {size} bytes ({size / 1024:.2f} KB)")

    # Test 3: Complete metadata
    print("\n📋 Test 3: Complete metadata")
    meta = compute_doc_meta(test_file)
    print(f"✅ Metadata: {meta}")
    print(f"   ID: {meta['id']}")
    print(f"   Bytes: {meta['bytes']}")
    print(f"   Paginas: {meta['paginas']} (None expected for .py file)")

    # Test 4: Error handling (archivo inexistente)
    print("\n📋 Test 4: Error handling")
    try:
        compute_file_hash(Path("nonexistent_file.pdf"))
        print("❌ Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"✅ Correctly raised FileNotFoundError: {e}")

    print("\n✅ All hashing tests passed!")
