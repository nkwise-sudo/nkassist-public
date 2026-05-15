# rag/rerank.py
"""
Rerank governado (V2) para resultados de RAG.

Problemas atacados:
- Score pode ficar negativo após rerank (dificulta confidence gating).
- FAISS puro traz proximidade semântica, mas pode errar intenção.
- Muitos resultados do mesmo documento ("monocultura do Manual TI").

Solução V2 (heurística transparente, sem LLM):
1) Keyword overlap (0..1) auditável
2) Penalidade de diversidade por repetição do mesmo doc_id (MMR simplificado)
3) Score final NORMALIZADO e estável em [0,1]
   - Mantém "rerank_raw" para auditoria
   - Expõe "semantic_score" e "keyword_score" em meta (quando possível)

Sem acoplamento ao agente/LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re

from rag.vectorstore_faiss import SearchResult


_STOPWORDS_PT = {
    "a", "o", "os", "as", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "sem", "um", "uma", "uns", "umas", "e", "ou", "que", "como",
    "qual", "quais", "onde", "quando", "porque", "porquê", "sobre", "isso", "isto", "essa",
    "esse", "essas", "esses", "ao", "à", "às"
}


def tokenize_pt(text: str) -> list[str]:
    """
    Tokenização simples (V2).
    Mantém letras/números, minúsculo, remove stopwords, remove tokens curtos (<3).
    """
    text = (text or "").lower()
    tokens = re.findall(r"[a-z0-9çãõáéíóúàêôû]+", text, flags=re.IGNORECASE)
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS_PT]


def keyword_overlap_score(query: str, chunk_text: str) -> float:
    """
    Score 0..1 baseado em overlap de tokens do query presentes no chunk.
    Transparente e auditável.
    """
    q = set(tokenize_pt(query))
    if not q:
        return 0.0
    t = set(tokenize_pt(chunk_text))
    hit = len(q.intersection(t))
    return hit / max(1, len(q))


def _sigmoid(x: float) -> float:
    """
    Comprime qualquer real para (0,1).
    Isso garante estabilidade do score para gating/telemetria.
    """
    # evita overflow em valores extremos
    if x >= 60:
        return 1.0
    if x <= -60:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _safe_float(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


@dataclass(frozen=True)
class RerankConfig:
    top_k: int
    alpha_semantic: float = 0.80
    beta_keyword: float = 0.20
    diversity_lambda: float = 0.25
    # score final em [0,1] por padrão (clamp defensivo)
    score_floor: float = 0.0
    score_ceil: float = 1.0


def rerank_results(
    query: str,
    results: list[SearchResult],
    *,
    top_k: int,
    alpha_semantic: float = 0.80,
    beta_keyword: float = 0.20,
    diversity_lambda: float = 0.25,
) -> list[SearchResult]:
    """
    Rerankeia resultados.

    raw = alpha*semantic + beta*keyword - diversity_penalty
    final = sigmoid(raw) -> [0,1]

    - "semantic" é o score do vector store (FAISS).
    - "keyword" é overlap 0..1.
    - "diversity_penalty" cresce conforme repetição do mesmo doc_id já selecionado.

    Observação:
    - Guardamos evidências do rerank em meta:
      semantic_score, keyword_score, rerank_raw, rerank_score
    """
    if not results:
        return []

    cfg = RerankConfig(
        top_k=top_k,
        alpha_semantic=alpha_semantic,
        beta_keyword=beta_keyword,
        diversity_lambda=diversity_lambda,
    )

    # Pré-calcula keyword score
    kw_scores = [keyword_overlap_score(query, r.text) for r in results]

    # Score base combinado (antes de diversidade)
    combined: list[tuple[float, float, SearchResult]] = []
    for r, kw in zip(results, kw_scores):
        sem = _safe_float(r.score)
        base = (cfg.alpha_semantic * sem) + (cfg.beta_keyword * _safe_float(kw))
        combined.append((base, kw, r))

    # Ordena por base
    combined.sort(key=lambda x: x[0], reverse=True)

    chosen: list[SearchResult] = []
    seen_docs: dict[str, int] = {}

    for base, kw, r in combined:
        doc_count = seen_docs.get(r.doc_id, 0)
        penalty = cfg.diversity_lambda * doc_count

        rerank_raw = base - penalty
        rerank_score = _sigmoid(rerank_raw)
        rerank_score = max(cfg.score_floor, min(cfg.score_ceil, rerank_score))

        # meta auditável sem quebrar compatibilidade
        meta = dict(r.meta or {})
        meta.update(
            {
                "semantic_score": _safe_float(r.score),
                "keyword_score": _safe_float(kw),
                "rerank_raw": rerank_raw,
                "rerank_score": rerank_score,
                "diversity_doc_count": doc_count,
                "diversity_penalty": penalty,
            }
        )

        r2 = SearchResult(
            score=rerank_score,  # agora é o score final normalizado
            chunk_id=r.chunk_id,
            doc_id=r.doc_id,
            source_path=r.source_path,
            title=r.title,
            text=r.text,
            start_char=r.start_char,
            end_char=r.end_char,
            meta=meta,
        )
        chosen.append(r2)
        seen_docs[r.doc_id] = doc_count + 1

        if len(chosen) >= cfg.top_k:
            break

    chosen.sort(key=lambda x: _safe_float(x.score), reverse=True)
    return chosen