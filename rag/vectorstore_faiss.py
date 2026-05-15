# rag/vectorstore_faiss.py
"""
Vector Store FAISS (V1) + OpenAI Embeddings

Objetivo:
- Construir um índice FAISS a partir do corpus.jsonl
- Persistir:
  - data/faiss.index
  - data/faiss_meta.jsonl
- Buscar por similaridade:
  - search(query, top_k) -> retorna chunks + score + metadados (citações)

Design:
- IndexFlatIP (Inner Product) + vetores normalizados => similaridade por cosseno.
- Meta separado em JSONL para manter o índice leve.
- Rebuild total (V1) para simplicidade; depois evoluímos pra incremental.

Requisitos:
- env: OPENAI_API_KEY
- recomendado: NKASSIST_EMBED_MODEL (default text-embedding-3-large)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

import numpy as np

# Carrega .env do diretório raiz do projeto (dois níveis acima de rag/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except Exception:
    pass


# ------------------------
# Models
# ------------------------

@dataclass(frozen=True)
class SearchResult:
    score: float
    chunk_id: str
    doc_id: str
    source_path: str
    title: str | None
    text: str
    start_char: int
    end_char: int
    meta: dict[str, Any]


# ------------------------
# Utils
# ------------------------

def _safe_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(_safe_json_dumps(r) + "\n")
    tmp.replace(path)


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    """
    Normaliza vetores para norma 1 (para cos sim via inner product).
    """
    norm = np.linalg.norm(v, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return v / norm


# ------------------------
# OpenAI Embeddings
# ------------------------

def embed_texts(texts: list[str], model: str) -> np.ndarray:
    """
    Gera embeddings via OpenAI.

    Retorna np.ndarray shape (n, dim) float32.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não encontrado no ambiente (.env carregado?)")

    # SDK moderno (openai>=1.x)
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key)

    # A API aceita batching; vamos em lotes pequenos para estabilidade
    vectors: list[list[float]] = []
    batch_size = 64

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        # mantém ordem
        vectors.extend([d.embedding for d in resp.data])

    arr = np.array(vectors, dtype=np.float32)
    return arr


# ------------------------
# FAISS Store
# ------------------------

class FaissVectorStore:
    """
    Store FAISS com persistência de índice + metadados JSONL.
    """

    def __init__(self, *, index_path: Path, meta_path: Path, embed_model: str) -> None:
        self.index_path = index_path
        self.meta_path = meta_path
        self.embed_model = embed_model

        self._index = None  # carregado sob demanda
        self._meta: list[dict[str, Any]] = []

    def build_from_corpus(self, corpus_path: Path) -> dict[str, Any]:
        """
        Constrói índice a partir do corpus.jsonl e persiste em disco.
        """
        rows = _read_jsonl(corpus_path)
        if not rows:
            raise RuntimeError(f"Corpus vazio ou inexistente: {corpus_path}")

        texts = [r.get("text", "") for r in rows]
        # Filtra vazios (por segurança)
        keep = [i for i, t in enumerate(texts) if isinstance(t, str) and t.strip()]
        rows = [rows[i] for i in keep]
        texts = [texts[i] for i in keep]

        emb = embed_texts(texts, model=self.embed_model)
        emb = _l2_normalize(emb)

        # Importa faiss apenas quando necessário (evita erro em ambientes sem lib)
        import faiss  # type: ignore

        dim = emb.shape[1]
        index = faiss.IndexFlatIP(dim)  # inner product == cosine se normalizado
        index.add(emb)

        # Persistência
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.index_path))
        _write_jsonl(self.meta_path, rows)

        # Mantém em memória também
        self._index = index
        self._meta = rows

        return {
            "corpus_rows": len(rows),
            "dim": int(dim),
            "index_path": str(self.index_path),
            "meta_path": str(self.meta_path),
            "embed_model": self.embed_model,
        }

    def load(self) -> None:
        """
        Carrega índice e metadados do disco.
        """
        import faiss  # type: ignore

        if not self.index_path.exists():
            raise RuntimeError(f"Índice FAISS não encontrado: {self.index_path}")
        if not self.meta_path.exists():
            raise RuntimeError(f"Meta não encontrada: {self.meta_path}")

        self._index = faiss.read_index(str(self.index_path))
        self._meta = _read_jsonl(self.meta_path)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        Busca top_k chunks mais similares ao query.
        Retorna resultados com score (0..1 aprox) e metadados para citação.
        """
        if self._index is None or not self._meta:
            self.load()

        q_emb = embed_texts([query], model=self.embed_model)
        q_emb = _l2_normalize(q_emb)

        # FAISS: retorna (scores, indices)
        scores, idxs = self._index.search(q_emb, top_k)

        results: list[SearchResult] = []
        for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
            if idx < 0 or idx >= len(self._meta):
                continue
            m = self._meta[idx]
            results.append(
                SearchResult(
                    score=float(score),
                    chunk_id=m.get("chunk_id"),
                    doc_id=m.get("doc_id"),
                    source_path=m.get("source_path"),
                    title=m.get("title"),
                    text=m.get("text"),
                    start_char=int(m.get("start_char", 0)),
                    end_char=int(m.get("end_char", 0)),
                    meta=m.get("meta", {}) or {},
                )
            )

        return results


# ------------------------
# Bootstrap helper
# ------------------------

def build_faiss_store_from_env(project_root: Path) -> FaissVectorStore:
    """
    Usa .env:
    - NKASSIST_DATA_DIR
    - NKASSIST_FAISS_INDEX_PATH
    - NKASSIST_FAISS_META_PATH
    - NKASSIST_EMBED_MODEL
    """
    data_dir = Path(os.getenv("NKASSIST_DATA_DIR", str(project_root / "data")))

    index_path = Path(os.getenv("NKASSIST_FAISS_INDEX_PATH", str(data_dir / "faiss.index")))
    meta_path = Path(os.getenv("NKASSIST_FAISS_META_PATH", str(data_dir / "faiss_meta.jsonl")))
    embed_model = os.getenv("NKASSIST_EMBED_MODEL", "text-embedding-3-large")

    return FaissVectorStore(index_path=index_path, meta_path=meta_path, embed_model=embed_model)