# rag/ingest.py
"""
RAG - Ingestão de documentos (V1)

Objetivo:
- Ler documentos do diretório knowledge/
- Normalizar texto (mínimo)
- Fazer chunking (tamanho + overlap)
- Salvar "corpus" em JSONL com metadados, pronto pra indexação (embeddings depois)

Saída:
- data/corpus.jsonl  (1 chunk por linha)

Regras de arquitetura:
- Este módulo NÃO executa ingestão automaticamente ao ser importado.
- Execução fica em scripts de teste/CLI (ex: rag/teste_ingest.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import os
import re

from rag.parsers import read_document

from dotenv import load_dotenv

# Carrega .env do diretório raiz do projeto (dois níveis acima de rag/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ------------------------
# Modelos de dados
# ------------------------

@dataclass(frozen=True)
class Chunk:
    """
    Um chunk é a unidade que será vetorizada no futuro.
    """
    schema: str
    chunk_id: str
    doc_id: str
    source_path: str
    title: str | None
    text: str
    start_char: int
    end_char: int
    meta: dict[str, Any]


# ------------------------
# Helpers básicos
# ------------------------

# Regex para capturar wikilinks do Obsidian, com suporte a:
# [[doc]]
# [[doc#secao]]
# [[doc|alias]]
# [[doc#secao|alias]]
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

# Regex para capturar tags Obsidian / markdown tipo:
# #lagm
# #lagm/pillar
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_/\-]+)")


def normalize_doc_name(name: str) -> str:
    """
    Normaliza nomes de documentos para comparação semântica posterior.

    Exemplo:
    'Human_in_the_Loop' -> 'human in the loop'
    """
    name = name.strip().lower()
    name = name.replace("\\", "/")
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)
    return name


def extract_obsidian_links(text: str) -> list[str]:
    """
    Extrai wikilinks [[...]] do conteúdo markdown.
    Remove duplicados preservando ordem.
    """
    links: list[str] = []
    for match in WIKILINK_RE.findall(text):
        cleaned = match.strip()
        if cleaned:
            links.append(cleaned)

    seen = set()
    result: list[str] = []
    for item in links:
        key = normalize_doc_name(item)
        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


def extract_obsidian_tags(text: str) -> list[str]:
    """
    Extrai tags estilo Obsidian/Markdown do texto.
    Remove duplicados preservando ordem.
    """
    tags = TAG_RE.findall(text)

    seen = set()
    result: list[str] = []
    for tag in tags:
        cleaned = tag.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)

    return result


def _safe_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def file_sha1(path: Path) -> str:
    """
    Hash do conteúdo do arquivo.
    Serve como doc_id determinístico (se mudar conteúdo, muda id).
    """
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_text(text: str) -> str:
    """
    Normalização mínima (sem destruir informação).
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[tuple[int, int, str]]:
    """
    Chunking por caracteres com overlap (V1).
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser > 0")
    if overlap < 0:
        raise ValueError("overlap deve ser >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap deve ser menor que chunk_size")

    chunks: list[tuple[int, int, str]] = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + chunk_size, n)
        piece = text[start:end]
        if piece.strip():
            chunks.append((start, end, piece))

        if end == n:
            break
        start = end - overlap

    return chunks


# ------------------------
# Ingestor
# ------------------------

class Ingestor:
    """
    Faz ingestão do diretório knowledge/ e gera corpus.jsonl
    """

    def __init__(
        self,
        *,
        knowledge_dir: Path,
        output_corpus_path: Path,
        allowed_ext: tuple[str, ...] = (".md", ".txt", ".pdf"),
        chunk_size: int = 900,
        overlap: int = 150,
        excluded_dirs: frozenset[str] = frozenset(),
    ) -> None:
        self.knowledge_dir = knowledge_dir
        self.output_corpus_path = output_corpus_path
        self.allowed_ext = tuple(e.lower() for e in allowed_ext)
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.excluded_dirs = excluded_dirs

        self.output_corpus_path.parent.mkdir(parents=True, exist_ok=True)

    def iter_documents(self) -> Iterable[Path]:
        """
        Varre knowledge_dir recursivamente e retorna arquivos elegíveis.

        Diretórios listados em self.excluded_dirs são ignorados em qualquer
        nível da hierarquia (ex: 'versions', 'archive', '.git').
        """
        if not self.knowledge_dir.exists():
            return []
        files: list[Path] = []
        for p in self.knowledge_dir.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in self.allowed_ext:
                continue
            # Verifica se algum componente do caminho relativo é excluído
            relative = p.relative_to(self.knowledge_dir)
            if any(part in self.excluded_dirs for part in relative.parts):
                continue
            files.append(p)
        return sorted(files)

    def ingest(self) -> dict[str, Any]:
        """
        Estratégia V1: recria o corpus inteiro.
        """
        docs = list(self.iter_documents())
        written = 0
        tmp_path = self.output_corpus_path.with_suffix(".jsonl.tmp")

        with tmp_path.open("w", encoding="utf-8") as out:
            for doc_path in docs:
                doc_id = file_sha1(doc_path)

                # Lê conforme extensão (txt/md/pdf/docx/etc, conforme parser suportar)
                raw = read_document(doc_path)
                text = normalize_text(raw)

                # Se não conseguiu extrair texto (PDF escaneado, por exemplo),
                # ainda registramos no resumo pela contagem de docs, mas não gera chunks.
                if not text:
                    continue

                title = self._infer_title(doc_path, text)
                pieces = chunk_text(text, chunk_size=self.chunk_size, overlap=self.overlap)

                ext = doc_path.suffix.lower()
                obsidian_links = extract_obsidian_links(text) if ext == ".md" else []
                obsidian_tags = extract_obsidian_tags(text) if ext == ".md" else []

                source_path = str(doc_path.relative_to(self.knowledge_dir))

                base_meta = {
                    "ext": ext,
                    "bytes": doc_path.stat().st_size,
                    "obsidian_links": obsidian_links,
                    "obsidian_tags": obsidian_tags,
                }

                for (start, end, piece) in pieces:
                    chunk_id = sha1_hex(f"{doc_id}:{start}:{end}")

                    chunk = Chunk(
                        schema="nkassist.rag.chunk.v1",
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        source_path=source_path,
                        title=title,
                        text=piece,
                        start_char=start,
                        end_char=end,
                        meta=base_meta,
                    )

                    out.write(_safe_json_dumps(chunk.__dict__) + "\n")
                    written += 1

        tmp_path.replace(self.output_corpus_path)

        return {
            "documents": len(docs),
            "chunks_written": written,
            "corpus_path": str(self.output_corpus_path),
            "allowed_ext": list(self.allowed_ext),
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "excluded_dirs": sorted(self.excluded_dirs),
        }

    def _infer_title(self, doc_path: Path, text: str) -> str | None:
        if doc_path.suffix.lower() == ".md":
            for line in text.splitlines()[:20]:
                s = line.strip()
                if s.startswith("#"):
                    return s.lstrip("#").strip() or doc_path.stem
        return doc_path.stem


# ------------------------
# Bootstrap helper
# ------------------------

def build_ingestor_from_env(project_root: Path) -> Ingestor:
    """
    Constrói o Ingestor usando env vars (compatível com nosso .env).

    Env vars:
    - NKASSIST_KNOWLEDGE_DIR
    - NKASSIST_DATA_DIR
    - NKASSIST_ALLOWED_EXT      (ex: ".md,.txt,.pdf")
    - NKASSIST_CHUNK_SIZE
    - NKASSIST_CHUNK_OVERLAP
    - NKASSIST_EXCLUDED_DIRS    (ex: "versions,archive,.git")
    """
    knowledge_dir = Path(os.getenv("NKASSIST_KNOWLEDGE_DIR", str(project_root / "knowledge")))
    data_dir = Path(os.getenv("NKASSIST_DATA_DIR", str(project_root / "data")))
    corpus_path = data_dir / "corpus.jsonl"

    allowed_ext_raw = os.getenv("NKASSIST_ALLOWED_EXT", ".md,.txt")
    allowed_ext = tuple(e.strip().lower() for e in allowed_ext_raw.split(",") if e.strip())

    excluded_dirs_raw = os.getenv("NKASSIST_EXCLUDED_DIRS", "")
    excluded_dirs = frozenset(
        d.strip() for d in excluded_dirs_raw.split(",") if d.strip()
    )

    try:
        chunk_size = int(os.getenv("NKASSIST_CHUNK_SIZE", "900"))
    except ValueError:
        chunk_size = 900

    try:
        overlap = int(os.getenv("NKASSIST_CHUNK_OVERLAP", "150"))
    except ValueError:
        overlap = 150

    return Ingestor(
        knowledge_dir=knowledge_dir,
        output_corpus_path=corpus_path,
        allowed_ext=allowed_ext,
        chunk_size=chunk_size,
        overlap=overlap,
        excluded_dirs=excluded_dirs,
    )
