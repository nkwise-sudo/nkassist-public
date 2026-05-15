# rag/parsers.py
"""
Parsers de documentos para RAG (V1)

Objetivo:
- Extrair texto de diferentes formatos de arquivo de forma previsível.
- Começamos com:
  - .txt / .md : leitura direta
  - .pdf      : extração via pypdf (sem OCR)

Obs:
- PDFs "scanned" (imagem) podem retornar pouco/zero texto.
  Aí sim a gente avalia OCR (último recurso).
"""

from __future__ import annotations

from pathlib import Path


def read_document(path: Path) -> str:
    """
    Roteador principal: escolhe o parser baseado na extensão.
    Retorna texto (string). Se não suportado, levanta ValueError.
    """
    ext = path.suffix.lower()

    if ext in (".txt", ".md"):
        return _read_text(path)

    if ext == ".pdf":
        return _read_pdf(path)

    raise ValueError(f"Extensão não suportada: {ext}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    """
    Extrai texto de PDF usando pypdf.

    Importante:
    - Funciona bem para PDFs com texto "de verdade".
    - Pode falhar/retornar vazio para PDFs escaneados (imagem).
    """
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "pypdf não está instalado. Rode: pip install pypdf"
        ) from e

    reader = PdfReader(str(path))
    parts: list[str] = []

    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        txt = txt.strip()
        if txt:
            parts.append(txt)

    return "\n\n".join(parts)