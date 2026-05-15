from __future__ import annotations

from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
import re


# ============================================================
# NKassist - Synthesis Engine v0
# ------------------------------------------------------------
# Objetivo:
#   Implementar a primeira camada de síntese governada do NKassist
#   sobre os resultados estruturados do retriever.
#
# Princípios:
#   - raw_results é a fonte oficial da síntese
#   - context_text NÃO é a interface principal da síntese
#   - fatos devem vir do corpus recuperado
#   - explicações podem ser adicionadas depois, sob política explícita
#   - tudo deve ser auditável
#
# Estado atual desta versão:
#   - sem chamada real a LLM
#   - draft baseado em chunks recuperados
#   - validator estrutural
#   - critic heurístico
#   - evidence log completo
#
# Evolução futura:
#   - trocar _draft_answer_from_chunks por chamada LLM
#   - adicionar claim tagging fino
#   - adicionar risk gate / HITL
# ============================================================


# -----------------------------
# Modelos internos do pipeline
# -----------------------------

@dataclass
class RetrievedChunk:
    chunk_id: str
    source_path: str
    text: str
    score: float | None = None
    rerank_score: float | None = None
    graph_bonus: float | None = None
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DraftAnswer:
    answer_text: str
    used_chunk_ids: list[str] = field(default_factory=list)
    used_sources: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    status: str  # ok | warning | fail
    issues: list[str] = field(default_factory=list)
    grounded_chunk_ids: list[str] = field(default_factory=list)
    coverage_ratio: float = 0.0


@dataclass
class CriticResult:
    status: str  # ok | warning | fail
    notes: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


@dataclass
class ClaimRecord:
    text: str
    label: str  # grounded | derived | parametric | unverified_external
    evidence_chunk_ids: list[str] = field(default_factory=list)
    source_paths: list[str] = field(default_factory=list)
    hitl_required: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class EvidenceLog:
    timestamp_utc: str
    query: str
    retrieval_summary: dict[str, Any]
    draft_summary: dict[str, Any]
    validation_summary: dict[str, Any]
    critic_summary: dict[str, Any]
    final_summary: dict[str, Any]
    claims: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SynthesisResult:
    draft_answer: str | None
    final_answer: str
    validator_status: str
    critic_status: str
    critic_notes: list[str] = field(default_factory=list)
    claims: list[ClaimRecord] = field(default_factory=list)
    evidence_log: dict[str, Any] = field(default_factory=dict)
    used_fallback: bool = False
    # Campos do validator semântico (Fix 2)
    semantic_ok: bool = True
    semantic_issues: list[dict[str, Any]] = field(default_factory=list)
    semantic_confidence: float = 1.0
    semantic_model: str = ""
    semantic_skipped: bool = False
    semantic_skip_reason: str = ""


# -----------------------------
# Helpers de normalização
# -----------------------------

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(item: Any) -> dict[str, Any]:
    """
    Converte dict / dataclass / objeto simples em dict.
    """
    if item is None:
        return {}

    if isinstance(item, dict):
        return item

    if is_dataclass(item):
        return asdict(item)

    if hasattr(item, "model_dump"):
        try:
            return item.model_dump()
        except Exception:
            pass

    data: dict[str, Any] = {}
    for attr in dir(item):
        if attr.startswith("_"):
            continue
        try:
            value = getattr(item, attr)
        except Exception:
            continue
        if callable(value):
            continue
        data[attr] = value
    return data


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _normalize_chunk(item: Any) -> RetrievedChunk:
    """
    Normaliza um raw_result do retriever em RetrievedChunk.
    Aceita dict, dataclass ou objeto simples.
    """
    data = _as_dict(item)

    chunk_id = (
        _safe_str(data.get("chunk_id"))
        or _safe_str(data.get("id"))
        or _safe_str(data.get("doc_id"))
        or "unknown_chunk"
    )

    source_path = (
        _safe_str(data.get("source_path"))
        or _safe_str(data.get("source"))
        or _safe_str(data.get("document"))
        or "unknown_source"
    )

    text = (
        _safe_str(data.get("text"))
        or _safe_str(data.get("content"))
        or _safe_str(data.get("snippet"))
        or ""
    )

    title = _safe_str(data.get("title")) or None

    score = _safe_float(data.get("score"))
    rerank_score = _safe_float(data.get("rerank_score"))
    graph_bonus = _safe_float(data.get("graph_bonus"))

    metadata = dict(data)
    return RetrievedChunk(
        chunk_id=chunk_id,
        source_path=source_path,
        text=text,
        score=score,
        rerank_score=rerank_score,
        graph_bonus=graph_bonus,
        title=title,
        metadata=metadata,
    )

# -----------------------------
# Helpers de síntese
# -----------------------------

def _normalize_spaces(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _clean_markdown_noise(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""

    # remove wikilinks básicos
    t = t.replace("[[", "").replace("]]", "")

    cleaned_lines: list[str] = []
    for raw_line in t.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "---":
            continue
        if line.startswith("#") and not line.lower().startswith("# lagm"):
            # remove headings auxiliares tipo ## Problem, ## Definition etc.
            continue
        if line.startswith("#"):
            line = line.lstrip("#").strip()
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def _first_meaningful_lines(text: str, max_lines: int = 6) -> list[str]:
    cleaned = _clean_markdown_noise(text)
    if not cleaned:
        return []

    out: list[str] = []
    for line in cleaned.splitlines():
        line = _normalize_spaces(line)
        if not line:
            continue
        if len(line) < 4:
            continue
        out.append(line)
        if len(out) >= max_lines:
            break
    return out


def _is_definition_query(query: str) -> bool:
    q = _normalize_spaces(query).lower()
    patterns = [
        "o que é",
        "o que sao",
        "o que são",
        "defina",
        "conceito de",
        "explique o que é",
        "explique o que sao",
        "explique o que são",
    ]
    return any(q.startswith(p) for p in patterns)


def _chunk_relevance_hint(chunk: RetrievedChunk, query: str) -> int:
    """
    Score heurístico auxiliar para selecionar chunks mais úteis para síntese.
    Não substitui score do retriever; só ajuda a escolher melhor material textual.
    """
    text = _clean_markdown_noise(chunk.text).lower()
    source = (chunk.source_path or "").lower()
    q = _normalize_spaces(query).lower()

    score = 0

    if _is_definition_query(query):
        if " is a " in text and "lagm" in text:
            score += 6
        if " é um " in text and "lagm" in text:
            score += 6
        if "definition" in text:
            score += 4
        if "manifesto" in source:
            score += 4
        if "technical_pillars" in source or "technical pillars" in source:
            score += 2

    if q and q in text:
        score += 2

    if len(text) > 80:
        score += 1

    if _looks_like_noise(text):
        score -= 3

    return score


def _select_chunks_for_synthesis(query: str, chunks: list[RetrievedChunk], max_chunks: int = 3) -> list[RetrievedChunk]:
    ranked = sorted(
        chunks,
        key=lambda c: (
            _chunk_relevance_hint(c, query),
            float(c.score or 0.0),
        ),
        reverse=True,
    )
    return ranked[:max_chunks]


def _compress_chunk_text(chunk: RetrievedChunk, max_lines: int = 4) -> str:
    lines = _first_meaningful_lines(chunk.text, max_lines=max_lines)
    if not lines:
        return ""
    return " ".join(lines).strip()

def _extract_definition_line(text: str) -> str:
    cleaned = _clean_markdown_noise(text)
    if not cleaned:
        return ""

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    for idx, line in enumerate(lines):
        lower = line.lower()

        if " is a " in lower and "lagm" in lower:
            return _normalize_spaces(line)

        if " é um " in lower and "lagm" in lower:
            return _normalize_spaces(line)

        if "designed to ensure" in lower and "lagm" in lower:
            return _normalize_spaces(line)

        if lower.startswith("definition") and idx + 1 < len(lines):
            return _normalize_spaces(lines[idx + 1])

    return ""


def _extract_bullets(text: str, max_items: int = 4) -> list[str]:
    cleaned = _clean_markdown_noise(text)
    if not cleaned:
        return []

    items: list[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            item = _normalize_spaces(stripped.lstrip("-").strip())
            if item and len(item) > 3:
                items.append(item)
            if len(items) >= max_items:
                break
    return items


def _looks_like_noise(text: str) -> bool:
    t = _normalize_spaces(text).lower()
    if not t:
        return True

    noisy_patterns = [
        "alteração retroativa",
        "referência obrigatória de versão",
        "registro de override humano",
        "capacidade de reprocessamento",
        "linked_by_peer",
    ]
    return any(p in t for p in noisy_patterns)

def _build_definition_answer(query: str, chunks: list[RetrievedChunk]) -> str:
    """
    Gera resposta curta e mais limpa para perguntas definicionais.
    Prioriza:
      1. linha de definição explícita
      2. bullets de características
      3. evidências
    """
    definition = ""
    characteristics: list[str] = []

    for chunk in chunks:
        if not definition:
            definition = _extract_definition_line(chunk.text)

        bullets = _extract_bullets(chunk.text, max_items=6)
        for bullet in bullets:
            if bullet not in characteristics and not _looks_like_noise(bullet):
                characteristics.append(bullet)

    lines: list[str] = []

    if definition:
        lines.append(definition)
    else:
        primary = _compress_chunk_text(chunks[0], max_lines=3)
        if primary:
            lines.append(primary)
        else:
            lines.append(
                f"Com base no corpus recuperado, encontrei referências relevantes para responder à pergunta: {query}."
            )

    if characteristics:
        lines.append("")
        lines.append("Principais características identificadas no corpus:")
        for item in characteristics[:5]:
            lines.append(f"- {item}")

    lines.append("")
    lines.append("Evidências principais:")
    for chunk in chunks[:3]:
        src = chunk.source_path
        if chunk.score is not None:
            lines.append(f"- {src} (score={chunk.score:.4f})")
        else:
            lines.append(f"- {src}")

    return "\n".join(lines).strip()


def _build_general_answer(query: str, chunks: list[RetrievedChunk]) -> str:
    """
    Gera resposta curta e legível para perguntas gerais,
    ainda sem LLM real.
    """
    lines: list[str] = []
    lines.append(f"Resposta baseada no contexto recuperado para: {query}")
    lines.append("")

    summary_parts: list[str] = []
    for chunk in chunks[:3]:
        piece = _compress_chunk_text(chunk, max_lines=3)
        if piece:
            summary_parts.append(piece)

    if summary_parts:
        lines.append("Síntese:")
        for piece in summary_parts:
            lines.append(f"- {piece}")

    lines.append("")
    lines.append("Evidências principais:")
    for chunk in chunks[:3]:
        src = chunk.source_path
        if chunk.score is not None:
            lines.append(f"- {src} (score={chunk.score:.4f})")
        else:
            lines.append(f"- {src}")

    return "\n".join(lines).strip()


def _normalize_chunks(raw_results: Iterable[Any]) -> list[RetrievedChunk]:
    chunks: list[RetrievedChunk] = []
    for item in raw_results:
        chunk = _normalize_chunk(item)
        if chunk.text.strip():
            chunks.append(chunk)
    return chunks




# -----------------------------
# Draft
# -----------------------------

def _draft_answer_from_chunks(query: str, chunks: list[RetrievedChunk], max_chunks: int = 3) -> DraftAnswer:
    """
    Draft v1:
      - ainda sem LLM real
      - seleciona chunks mais úteis para síntese
      - responde em formato resumido e legível
      - preserva governança e evidência explícita

    Futuro:
      substituir esta função por chamada real ao LLM,
      mantendo a mesma assinatura lógica.
    """
    if not chunks:
        return DraftAnswer(
            answer_text=(
                f"Não encontrei evidências suficientes no corpus para responder com segurança à pergunta: '{query}'."
            ),
            notes=["draft_sem_chunks"],
        )

    selected = _select_chunks_for_synthesis(query=query, chunks=chunks, max_chunks=max_chunks)
    used_chunk_ids = [c.chunk_id for c in selected]
    used_sources = list(dict.fromkeys(c.source_path for c in selected))

    if _is_definition_query(query):
        answer_text = _build_definition_answer(query=query, chunks=selected)
        notes = ["draft_v1_sem_llm", "query_type=definition", f"selected_chunks={len(selected)}"]
    else:
        answer_text = _build_general_answer(query=query, chunks=selected)
        notes = ["draft_v1_sem_llm", "query_type=general", f"selected_chunks={len(selected)}"]

    return DraftAnswer(
        answer_text=answer_text,
        used_chunk_ids=used_chunk_ids,
        used_sources=used_sources,
        notes=notes,
    )


# -----------------------------
# Validator
# -----------------------------

def _validate_answer(
    draft: DraftAnswer,
    chunks: list[RetrievedChunk],
) -> ValidationResult:
    """
    Validator v0:
      - estrutural, não semântico fino
      - verifica se há chunks
      - verifica se o draft referencia base recuperada
      - coverage_ratio = chunks usados / chunks disponíveis
    """
    if not chunks:
        return ValidationResult(
            status="fail",
            issues=["no_retrieved_chunks"],
            grounded_chunk_ids=[],
            coverage_ratio=0.0,
        )

    if not draft.answer_text.strip():
        return ValidationResult(
            status="fail",
            issues=["empty_draft_answer"],
            grounded_chunk_ids=[],
            coverage_ratio=0.0,
        )

    available_ids = {c.chunk_id for c in chunks}
    used_ids = [cid for cid in draft.used_chunk_ids if cid in available_ids]

    if not used_ids:
        return ValidationResult(
            status="warning",
            issues=["draft_without_explicit_chunk_usage"],
            grounded_chunk_ids=[],
            coverage_ratio=0.0,
        )

    coverage_ratio = round(len(set(used_ids)) / max(len(chunks), 1), 4)

    issues: list[str] = []
    status = "ok"

    if coverage_ratio < 0.20:
        status = "warning"
        issues.append("low_chunk_coverage")

    return ValidationResult(
        status=status,
        issues=issues,
        grounded_chunk_ids=used_ids,
        coverage_ratio=coverage_ratio,
    )


# -----------------------------
# Claim Tagger v0
# -----------------------------

def _build_claims(
    draft: DraftAnswer,
    chunks: list[RetrievedChunk],
    validation: ValidationResult,
) -> list[ClaimRecord]:
    """
    Claim tagging v0 simplificado:
      - trata o draft inteiro como uma claim grounded quando validado
      - fallback para unverified_external em casos anômalos
    """
    if not draft.answer_text.strip():
        return []

    chunk_map = {c.chunk_id: c for c in chunks}
    source_paths = [
        chunk_map[cid].source_path
        for cid in validation.grounded_chunk_ids
        if cid in chunk_map
    ]

    if validation.status in {"ok", "warning"} and validation.grounded_chunk_ids:
        return [
            ClaimRecord(
                text=draft.answer_text,
                label="grounded",
                evidence_chunk_ids=validation.grounded_chunk_ids,
                source_paths=list(dict.fromkeys(source_paths)),
                hitl_required=False,
                notes=["claim_bundle_v0"],
            )
        ]

    return [
        ClaimRecord(
            text=draft.answer_text,
            label="unverified_external",
            evidence_chunk_ids=[],
            source_paths=[],
            hitl_required=True,
            notes=["draft_without_grounding"],
        )
    ]


# -----------------------------
# Critic
# -----------------------------

def _critic_answer(
    query: str,
    draft: DraftAnswer,
    chunks: list[RetrievedChunk],
    validation: ValidationResult,
    claims: list[ClaimRecord],
) -> CriticResult:
    """
    Critic v0:
      - heurístico
      - detecta risco por ausência de grounding
      - detecta cobertura baixa
      - detecta resposta sem evidência útil
    """
    notes: list[str] = []
    risk_flags: list[str] = []
    status = "ok"

    if not chunks:
        status = "fail"
        notes.append("critic_no_chunks")
        risk_flags.append("no_evidence")
        return CriticResult(status=status, notes=notes, risk_flags=risk_flags)

    if validation.status == "fail":
        status = "fail"
        notes.append("validator_failed")
        risk_flags.append("validation_failed")

    if validation.coverage_ratio < 0.20:
        status = "warning" if status != "fail" else status
        notes.append("low_grounding_coverage")
        risk_flags.append("low_coverage")

    if any(claim.hitl_required for claim in claims):
        status = "warning" if status != "fail" else status
        notes.append("claim_requires_hitl")
        risk_flags.append("hitl_candidate")

    # heurística simples: se a pergunta parece operacional e a evidência é fraca, elevar risco
    operational_keywords = [
        "config",
        "configuração",
        "deploy",
        "produção",
        "remover",
        "alterar",
        "mudar",
        "delete",
        "apagar",
        "risco",
        "impacto",
    ]
    q = query.lower()
    if any(k in q for k in operational_keywords) and validation.coverage_ratio < 0.35:
        status = "warning" if status != "fail" else status
        notes.append("operational_question_with_weak_evidence")
        risk_flags.append("operational_risk")

    if not notes:
        notes.append("critic_v0_no_major_issues")

    return CriticResult(status=status, notes=notes, risk_flags=risk_flags)


# -----------------------------
# Finalizer
# -----------------------------

def _finalize_answer(
    query: str,
    draft: DraftAnswer,
    validation: ValidationResult,
    critic: CriticResult,
    chunks: list[RetrievedChunk],
) -> str:
    """
    Final Answer v1:
      - conserva o draft
      - adiciona aviso de governança apenas quando necessário
      - evita duplicação desnecessária do conteúdo
    """
    if not chunks:
        return (
            f"Não encontrei evidências suficientes no corpus para responder com segurança à pergunta: '{query}'."
        )

    if critic.status == "fail":
        return (
            "Resposta bloqueada por falha de validação do pipeline.\n\n"
            "Motivo: evidência insuficiente ou draft sem grounding confiável."
        )

    if critic.status == "warning":
        return (
            "Resposta gerada com ressalvas.\n"
            "Use como apoio inicial, não como verdade operacional definitiva, até validação adicional.\n\n"
            f"{draft.answer_text}"
        ).strip()

    return draft.answer_text.strip()


# -----------------------------
# Evidence Log
# -----------------------------

def _generate_evidence_log(
    query: str,
    chunks: list[RetrievedChunk],
    draft: DraftAnswer,
    validation: ValidationResult,
    critic: CriticResult,
    final_answer: str,
    claims: list[ClaimRecord],
) -> EvidenceLog:
    retrieval_summary = {
        "retrieved_chunks_count": len(chunks),
        "chunk_ids": [c.chunk_id for c in chunks],
        "source_paths": list(dict.fromkeys(c.source_path for c in chunks)),
        "top_scores": [
            {
                "chunk_id": c.chunk_id,
                "score": c.score,
                "rerank_score": c.rerank_score,
                "graph_bonus": c.graph_bonus,
            }
            for c in chunks[:5]
        ],
    }

    draft_summary = {
        "draft_exists": bool(draft.answer_text.strip()),
        "used_chunk_ids": draft.used_chunk_ids,
        "used_sources": draft.used_sources,
        "notes": draft.notes,
    }

    validation_summary = {
        "status": validation.status,
        "issues": validation.issues,
        "grounded_chunk_ids": validation.grounded_chunk_ids,
        "coverage_ratio": validation.coverage_ratio,
    }

    critic_summary = {
        "status": critic.status,
        "notes": critic.notes,
        "risk_flags": critic.risk_flags,
    }

    final_summary = {
        "final_answer_preview": final_answer[:500],
        "final_answer_length": len(final_answer),
    }

    return EvidenceLog(
        timestamp_utc=_now_utc_iso(),
        query=query,
        retrieval_summary=retrieval_summary,
        draft_summary=draft_summary,
        validation_summary=validation_summary,
        critic_summary=critic_summary,
        final_summary=final_summary,
        claims=[asdict(c) for c in claims],
    )


# -----------------------------
# API principal do módulo
# -----------------------------

def run_synthesis_pipeline(
    query: str,
    raw_results: list[Any],
) -> SynthesisResult:
    """
    Interface oficial inicial da synthesis layer.

    Regra:
      - recebe raw_results estruturados do retriever
      - NÃO recebe context_text como fonte principal
    """
    chunks = _normalize_chunks(raw_results)

    if not chunks:
        final_answer = (
            f"Não encontrei evidências suficientes no corpus para responder com segurança à pergunta: '{query}'."
        )

        evidence = _generate_evidence_log(
            query=query,
            chunks=[],
            draft=DraftAnswer(answer_text="", notes=["empty_retrieval"]),
            validation=ValidationResult(
                status="fail",
                issues=["no_retrieved_chunks"],
                grounded_chunk_ids=[],
                coverage_ratio=0.0,
            ),
            critic=CriticResult(
                status="fail",
                notes=["critic_no_chunks"],
                risk_flags=["no_evidence"],
            ),
            final_answer=final_answer,
            claims=[],
        )

        return SynthesisResult(
            draft_answer=None,
            final_answer=final_answer,
            validator_status="fail",
            critic_status="fail",
            critic_notes=["critic_no_chunks"],
            claims=[],
            evidence_log=asdict(evidence),
            used_fallback=True,
        )

    draft = _draft_answer_from_chunks(query=query, chunks=chunks)
    validation = _validate_answer(draft=draft, chunks=chunks)
    claims = _build_claims(draft=draft, chunks=chunks, validation=validation)
    critic = _critic_answer(
        query=query,
        draft=draft,
        chunks=chunks,
        validation=validation,
        claims=claims,
    )
    final_answer = _finalize_answer(
        query=query,
        draft=draft,
        validation=validation,
        critic=critic,
        chunks=chunks,
    )
    evidence = _generate_evidence_log(
        query=query,
        chunks=chunks,
        draft=draft,
        validation=validation,
        critic=critic,
        final_answer=final_answer,
        claims=claims,
    )

    return SynthesisResult(
        draft_answer=draft.answer_text,
        final_answer=final_answer,
        validator_status=validation.status,
        critic_status=critic.status,
        critic_notes=critic.notes,
        claims=claims,
        evidence_log=asdict(evidence),
        used_fallback=False,
    )


def _extract_cited_chunk_ids(draft_text: str, chunks: list[RetrievedChunk]) -> list[str]:
    """
    Extrai chunk_ids efetivamente citados no draft via referências [Fonte N].
    O _llm_answer() instrui o modelo a usar [Fonte N] onde N é 1-based.
    Retorna lista vazia se o draft não contiver nenhuma referência explícita.
    """
    cited_indices = set(
        int(m) - 1
        for m in re.findall(r'\[Fonte\s+(\d+)\]', draft_text)
    )
    return [
        chunks[i].chunk_id
        for i in sorted(cited_indices)
        if 0 <= i < len(chunks)
    ]


def run_synthesis_with_draft(
    query: str,
    raw_results: list[Any],
    draft_text: str,
) -> SynthesisResult:
    """
    Variante do pipeline de síntese que aceita um draft pré-gerado
    (ex: resposta vinda de um LLM externo) e o submete ao pipeline
    de validação, crítica e evidence log.

    Uso esperado:
        llm_answer = assistant._llm_answer(...)
        synthesis = run_synthesis_with_draft(query, pack.raw_results, llm_answer)
        final_answer = synthesis.final_answer

    Não altera a geração de texto — apenas governa e audita.
    """
    chunks = _normalize_chunks(raw_results)

    # Fix 1: extrair chunk_ids efetivamente citados no draft via [Fonte N]
    # Em vez de passar todos os chunks como "usados", identificamos quais
    # o LLM realmente referenciou — o que ativa o validator estrutural.
    cited_ids = _extract_cited_chunk_ids(draft_text, chunks)
    used_chunk_ids = cited_ids if cited_ids else [c.chunk_id for c in chunks]
    notes = ["draft_from_llm"]
    if not cited_ids:
        notes.append("no_explicit_citations_in_draft")

    cited_sources = list(dict.fromkeys(
        chunks[int(m) - 1].source_path
        for m in re.findall(r'\[Fonte\s+(\d+)\]', draft_text)
        if 0 <= int(m) - 1 < len(chunks)
    ))

    draft = DraftAnswer(
        answer_text=draft_text,
        used_chunk_ids=used_chunk_ids,
        used_sources=cited_sources or list(dict.fromkeys(c.source_path for c in chunks)),
        notes=notes,
    )

    if not chunks:
        final_answer = (
            f"Não encontrei evidências suficientes no corpus para responder com segurança à pergunta: '{query}'."
        )
        empty_validation = ValidationResult(
            status="fail",
            issues=["no_retrieved_chunks"],
            grounded_chunk_ids=[],
            coverage_ratio=0.0,
        )
        empty_critic = CriticResult(
            status="fail",
            notes=["critic_no_chunks"],
            risk_flags=["no_evidence"],
        )
        evidence = _generate_evidence_log(
            query=query,
            chunks=[],
            draft=draft,
            validation=empty_validation,
            critic=empty_critic,
            final_answer=final_answer,
            claims=[],
        )
        return SynthesisResult(
            draft_answer=draft_text,
            final_answer=final_answer,
            validator_status="fail",
            critic_status="fail",
            critic_notes=["critic_no_chunks"],
            claims=[],
            evidence_log=asdict(evidence),
            used_fallback=True,
        )

    # Fix 2: validator semântico — verifica consistência de conteúdo
    # Executa antes do validator estrutural para registrar ambos no log
    from rag.semantic_validator import validate_semantics
    semantic_result = validate_semantics(
        query=query,
        draft_text=draft_text,
        chunks=chunks,
    )

    validation = _validate_answer(draft=draft, chunks=chunks)
    claims = _build_claims(draft=draft, chunks=chunks, validation=validation)
    critic = _critic_answer(
        query=query,
        draft=draft,
        chunks=chunks,
        validation=validation,
        claims=claims,
    )
    final_answer = _finalize_answer(
        query=query,
        draft=draft,
        validation=validation,
        critic=critic,
        chunks=chunks,
    )
    evidence = _generate_evidence_log(
        query=query,
        chunks=chunks,
        draft=draft,
        validation=validation,
        critic=critic,
        final_answer=final_answer,
        claims=claims,
    )

    return SynthesisResult(
        draft_answer=draft_text,
        final_answer=final_answer,
        validator_status=validation.status,
        critic_status=critic.status,
        critic_notes=critic.notes,
        claims=claims,
        evidence_log=asdict(evidence),
        used_fallback=False,
        semantic_ok=semantic_result.semantic_ok,
        semantic_issues=[i.__dict__ for i in semantic_result.issues],
        semantic_confidence=semantic_result.confidence,
        semantic_model=semantic_result.model_used,
        semantic_skipped=semantic_result.validation_skipped,
        semantic_skip_reason=semantic_result.skip_reason,
    )