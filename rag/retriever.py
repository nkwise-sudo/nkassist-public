# rag/retriever.py
"""
Retriever governado para RAG (V2)

Objetivo:
- Orquestrar busca no vector store (FAISS)
- Aplicar guardrails:
  - limitar número de fontes (NKASSIST_MAX_SOURCES)
  - exigir citações (NKASSIST_REQUIRE_CITATIONS)
  - rerank heurístico (opcional)
  - diversity cap por documento (evita monocultura)
  - snippet guard (evita fonte com snippet vazio)
  - multi-query retrieval heurístico (opcional)
  - graph bonus com links do Obsidian (opcional)
- Retornar pacote pronto para o agente:
  - context_text (para prompt)
  - citations (lista estruturada)
  - raw_results (para evidence)

Sem acoplamento ao LLM aqui.

Changelog:
- 2026-03-30: NKASSIST_FOCUS_MAX_SENTENCES configurável via .env (default=10)
"""

from core.evidence import build_evidence_logger, new_event_id

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Optional, Sequence
import os
import re

from rag.focus import focus_text
from rag.rerank import rerank_results
from rag.vectorstore_faiss import FaissVectorStore, SearchResult, build_faiss_store_from_env

@dataclass(frozen=True)
class Citation:
    source_path: str
    title: str | None
    chunk_id: str
    doc_id: str
    start_char: int
    end_char: int
    score: float


@dataclass(frozen=True)
class RetrievalPack:
    query: str
    context_text: str
    citations: list[Citation]
    raw_results: list[SearchResult]


def _env_flag(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "y", "on")


def _fallback_snippet(text: str, limit: int = 420) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    return t[:limit].strip()


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def normalize_doc_name(name: str) -> str:
    name = (name or "").strip().lower()
    name = name.replace("\\", "/")
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)
    return name


def source_path_to_doc_name(source_path: str) -> str:
    stem = Path(source_path).stem
    return normalize_doc_name(stem)


def expand_query(query: str) -> list[str]:
    q = _normalize_spaces(query)
    if not q:
        return []

    candidates = {q}
    q_lower = q.lower()

    replacements = [
        ("pilares", ["componentes", "fundamentos", "estrutura"]),
        ("técnicos", ["tecnicos"]),
        ("arquitetura", ["estrutura", "design", "modelo"]),
        ("modelo", ["estrutura", "arquitetura"]),
        ("decisão", ["decisao"]),
        ("imutável", ["imutavel"]),
        ("governança", ["governanca"]),
        ("restore", ["restauração", "recuperação"]),
        ("backup", ["cópia de segurança", "copia de seguranca"]),
        ("procedimento", ["runbook", "rotina", "fluxo"]),
        ("incidente", ["falha", "ocorrência", "ocorrencia"]),
        ("política", ["politica", "diretriz"]),
    ]

    for base, variants in replacements:
        if base in q_lower:
            for variant in variants:
                candidates.add(_normalize_spaces(re.sub(base, variant, q, flags=re.IGNORECASE)))

    if q_lower.startswith("quais são") or q_lower.startswith("quais sao"):
        simplified = re.sub(r"^quais\s+s(ã|a)o\s+", "", q, flags=re.IGNORECASE)
        simplified = _normalize_spaces(simplified)
        if simplified:
            candidates.add(simplified)

    ordered = []
    seen = set()
    for item in candidates:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(item)

    max_queries = 4
    return ordered[:max_queries]


def merge_and_deduplicate_results(results: list[SearchResult], top_k: int) -> list[SearchResult]:
    best_by_chunk: dict[str, SearchResult] = {}

    for r in results:
        existing = best_by_chunk.get(r.chunk_id)
        if existing is None or float(r.score) > float(existing.score):
            best_by_chunk[r.chunk_id] = r

    merged = sorted(best_by_chunk.values(), key=lambda x: float(x.score), reverse=True)
    return merged[:top_k]


def apply_obsidian_graph_bonus(results: list[SearchResult], bonus: float = 0.035) -> list[SearchResult]:
    linked_targets: set[str] = set()

    for item in results:
        meta = getattr(item, "meta", {}) or {}
        for link in meta.get("obsidian_links", []) or []:
            linked_targets.add(normalize_doc_name(link))

    boosted: list[SearchResult] = []

    for item in results:
        current_name = source_path_to_doc_name(getattr(item, "source_path", "") or "")
        current_score = float(getattr(item, "score", 0.0))

        reason = None
        graph_bonus = 0.0

        if current_name in linked_targets:
            graph_bonus = bonus
            reason = "linked_by_peer"

        boosted_item = replace(item, score=current_score + graph_bonus)

        try:
            meta = dict(getattr(boosted_item, "meta", {}) or {})
            meta["graph_bonus"] = graph_bonus
            meta["graph_bonus_reason"] = reason
            meta["normalized_doc_name"] = current_name
            boosted_item = replace(boosted_item, meta=meta)
        except Exception:
            pass

        boosted.append(boosted_item)

    boosted.sort(key=lambda x: float(getattr(x, "score", 0.0)), reverse=True)
    return boosted


def enforce_diversity(
    results: list[SearchResult],
    *,
    max_sources: int,
    max_per_doc: int,
) -> list[SearchResult]:
    out: list[SearchResult] = []
    per_doc: dict[str, int] = {}

    for r in results:
        doc = r.doc_id or "unknown"
        if per_doc.get(doc, 0) >= max_per_doc:
            continue
        out.append(r)
        per_doc[doc] = per_doc.get(doc, 0) + 1
        if len(out) >= max_sources:
            break

    return out


class Retriever:
    def __init__(
        self,
        *,
        store: FaissVectorStore,
        max_sources: int,
        require_citations: bool,
        max_per_doc: int = 2,
        focus_max_sentences: int = 10,
    ) -> None:
        self.store = store
        self.max_sources = max_sources
        self.require_citations = require_citations
        self.max_per_doc = max_per_doc
        self.focus_max_sentences = focus_max_sentences  # PATCH 2026-03-30
        project_root = Path(__file__).resolve().parent.parent
        evidence_dir = Path(os.getenv("NKASSIST_EVIDENCE_DIR", str(project_root / "evidence")))
        self.evidence = build_evidence_logger(evidence_dir)

    def retrieve(self, query: str, top_k: int | None = None) -> RetrievalPack:
        k = self.max_sources if top_k is None else min(int(top_k), self.max_sources)

        try:
            recall_mult = int(os.getenv("NKASSIST_RECALL_MULT", "4"))
        except ValueError:
            recall_mult = 4

        recall_mult = max(1, min(recall_mult, 10))
        recall_k = max(k, k * recall_mult)

        if _env_flag("NKASSIST_MULTI_QUERY", "true"):
            expanded_queries = expand_query(query)
        else:
            expanded_queries = [query]

        collected_results: list[SearchResult] = []
        for q in expanded_queries:
            collected_results.extend(self.store.search(q, top_k=recall_k))

        results = merge_and_deduplicate_results(collected_results, top_k=max(recall_k, k))

        if _env_flag("NKASSIST_RERANK", "true"):
            results = rerank_results(query, results, top_k=max(recall_k, k))

        if _env_flag("NKASSIST_OBSIDIAN_GRAPH_BONUS", "true"):
            try:
                graph_bonus = float(os.getenv("NKASSIST_OBSIDIAN_GRAPH_BONUS_VALUE", "0.035"))
            except ValueError:
                graph_bonus = 0.035

            graph_bonus = max(0.0, min(graph_bonus, 0.10))
            results = apply_obsidian_graph_bonus(results, bonus=graph_bonus)

        if _env_flag("NKASSIST_DIVERSITY_CAP", "true"):
            results = enforce_diversity(results, max_sources=k, max_per_doc=self.max_per_doc)
        else:
            results = results[:k]

        citations: list[Citation] = []
        blocks: list[str] = []

        for i, r in enumerate(results, start=1):
            c = Citation(
                source_path=r.source_path,
                title=r.title,
                chunk_id=r.chunk_id,
                doc_id=r.doc_id,
                start_char=r.start_char,
                end_char=r.end_char,
                score=float(r.score),
            )
            citations.append(c)

            header = (
                f"[Fonte {i}] {c.source_path} | {c.title or ''} | "
                f"score={c.score:.4f} | range={c.start_char}-{c.end_char} | chunk_id={c.chunk_id}"
            )

            # PATCH 2026-03-30: max_sentences configurável via NKASSIST_FOCUS_MAX_SENTENCES
            snippet = focus_text(query, r.text, max_sentences=self.focus_max_sentences)
            snippet = (snippet or "").strip()

            if not snippet:
                snippet = _fallback_snippet(r.text)

            if not snippet:
                snippet = "[snippet_unavailable]"

            blocks.append(header + "\n" + snippet)

        context_text = "\n\n---\n\n".join(blocks).strip()

        if self.require_citations and not citations:
            context_text = ""

        try:
            retrieval_event_id = new_event_id("rag")

            retrieval_results: list[dict[str, Any]] = []
            for rank, r in enumerate(results, start=1):
                meta = getattr(r, "meta", {}) or {}
                retrieval_results.append(
                    {
                        "rank": rank,
                        "chunk_id": r.chunk_id,
                        "doc_id": r.doc_id,
                        "source_path": r.source_path,
                        "title": r.title,
                        "score": float(r.score),
                        "start_char": r.start_char,
                        "end_char": r.end_char,
                        "graph_bonus_reason": meta.get("graph_bonus_reason"),
                        "normalized_doc_name": meta.get("normalized_doc_name"),
                        "graph_bonus": float(meta.get("graph_bonus", 0.0)),
                        "obsidian_links": meta.get("obsidian_links", []),
                        "obsidian_tags": meta.get("obsidian_tags", []),
                    }
                )

            self.evidence.log_rag_query(
                event_id=retrieval_event_id,
                query=query,
                top_k=k,
                results_count=len(results),
                results=retrieval_results,
                pipeline=(
                    "faiss_retriever_multiquery_graph"
                    if len(expanded_queries) > 1 and _env_flag("NKASSIST_OBSIDIAN_GRAPH_BONUS", "true")
                    else "faiss_retriever_graph"
                    if _env_flag("NKASSIST_OBSIDIAN_GRAPH_BONUS", "true")
                    else "faiss_retriever_multiquery"
                    if len(expanded_queries) > 1
                    else "faiss_retriever"
                ),
                comment=f"expanded_queries={expanded_queries}",
            )
        except Exception:
            pass

        return RetrievalPack(
            query=query,
            context_text=context_text,
            citations=citations,
            raw_results=results,
        )


def build_retriever_from_env(project_root: Path) -> Retriever:
    store = build_faiss_store_from_env(project_root)

    try:
        max_sources = int(os.getenv("NKASSIST_MAX_SOURCES", "6"))
    except ValueError:
        max_sources = 6

    require_citations = _env_flag("NKASSIST_REQUIRE_CITATIONS", "true")

    try:
        max_per_doc = int(os.getenv("NKASSIST_MAX_PER_DOC", "2"))
    except ValueError:
        max_per_doc = 2

    # PATCH 2026-03-30: lê NKASSIST_FOCUS_MAX_SENTENCES do .env (default=10)
    # Instância LAGM: sem esta variável = usa 10 (melhor que o antigo 6)
    # Instância MEDRIO: definir 12 no .env para máxima cobertura de listas
    try:
        focus_max_sentences = int(os.getenv("NKASSIST_FOCUS_MAX_SENTENCES", "10"))
    except ValueError:
        focus_max_sentences = 10

    return Retriever(
        store=store,
        max_sources=max_sources,
        require_citations=require_citations,
        max_per_doc=max_per_doc,
        focus_max_sentences=focus_max_sentences,
    )


def filter_pack_by_source_prefix(pack, prefixes: Sequence[str], top_k: Optional[int] = None):
    if not prefixes:
        return pack

    prefixes_norm = tuple(p if p.endswith("/") else p + "/" for p in prefixes)

    filtered = []
    for c in pack.citations:
        sp = getattr(c, "source_path", "") or ""
        if sp.startswith(prefixes_norm):
            filtered.append(c)

    if top_k is not None:
        filtered = filtered[:top_k]

    blocks = []
    for i, c in enumerate(filtered, start=1):
        title = getattr(c, "title", None) or "Sem título"
        score = getattr(c, "score", None)
        rng = getattr(c, "range", None) or getattr(c, "char_range", None)
        chunk_id = getattr(c, "chunk_id", None)

        header = f"[Fonte {i}] {c.source_path} | {title}"
        if score is not None:
            header += f" | score={score:.4f}"
        if rng is not None:
            header += f" | range={rng}"
        if chunk_id is not None:
            header += f" | chunk_id={chunk_id}"

        text = getattr(c, "text", "") or ""
        blocks.append(header + "\n" + text + "\n\n---\n")

    new_context = "\n".join(blocks).strip()
    return replace(pack, citations=filtered, context_text=new_context)
