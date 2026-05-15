# core/evidence.py
"""
Trilha de Evidências (append-only) para Governança + HITL.

Objetivo:
- Registrar eventos de forma auditável em JSONL:
  - decisions.jsonl  (decisões do agente, sempre com fontes/citações quando aplicável)
  - approvals.jsonl  (aprovações humanas / revisões)
  - actions.jsonl    (ações executadas — ou tentadas — por integrações)

Características:
- Append-only: nunca reescreve linhas, só adiciona.
- Estrutura consistente + metadados mínimos.
- Hash-chain opcional para detectar alteração (tamper-evidence) sem banco de dados.
  (Não impede alteração, mas deixa evidência de alteração.)

Formato JSONL:
- 1 JSON por linha.
- Fácil de fazer tail/grep/jq e de versionar/arquivar.

Dependências: apenas stdlib.
Compatível com Python 3.11+.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
import json
import hashlib
import os
import socket
import uuid
from datetime import datetime, timezone


EvidenceType = Literal["decision", "approval", "action", "rag_query"]


def utc_now_iso() -> str:
    """Timestamp UTC em ISO-8601 com timezone."""
    return datetime.now(timezone.utc).isoformat()


def _safe_json_dumps(obj: Any) -> str:
    """JSON determinístico (ajuda auditoria e hash)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_event_id(prefix: str = "evt") -> str:
    """
    Gera um event_id simples, único e legível.
    Ex: evt-4f9c2a1b
    """
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True)
class EvidencePaths:
    """
    Caminhos padrão para arquivos de evidência.
    Mantemos separado por tipo para evitar "tudo num saco só".
    """
    root: Path
    decisions: Path
    approvals: Path
    actions: Path
    rag_queries: Path
    chain_state: Path  # guarda o último hash por arquivo (opcional)


def build_evidence_paths(evidence_dir: Path) -> EvidencePaths:
    """
    Cria estrutura padrão de paths.
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return EvidencePaths(
        root=evidence_dir,
        decisions=evidence_dir / "decisions.jsonl",
        approvals=evidence_dir / "approvals.jsonl",
        actions=evidence_dir / "actions.jsonl",
        rag_queries=evidence_dir / "rag_queries.jsonl",
        chain_state=evidence_dir / "chain_state.json",
    )


class EvidenceLog:
    """
    Logger de evidências com append-only + hash-chain opcional.

    O hash-chain funciona assim:
    - Cada linha inclui "prev_hash" e "line_hash"
    - line_hash = sha256(prev_hash + canonical_json_without_line_hash)
    - Guardamos o último hash em chain_state.json para continuidade entre execuções.

    Benefício:
    - Se alguém editar uma linha no meio, a cadeia quebra.
    - Auditoria detecta, mesmo sem usar banco.
    """

    def __init__(
        self,
        paths: EvidencePaths,
        enable_hash_chain: bool = True,
        actor_default: str | None = None,
    ) -> None:
        self.paths = paths
        self.enable_hash_chain = enable_hash_chain
        self.actor_default = actor_default or os.getenv("USER") or "unknown"
        self.host = socket.gethostname()

        # garante que o state exista (ou inicialize)
        if self.enable_hash_chain and not self.paths.chain_state.exists():
            self._write_chain_state({})

    # ------------------------
    # API principal de registro
    # ------------------------

    def log_decision(
        self,
        *,
        event_id: str,
        decision_engine: str,
        decision: dict[str, Any],
        sources: list[dict[str, Any]] | None = None,
        confidence: float | None = None,
        risk_level: Literal["low", "medium", "high"] = "low",
        actor: str | None = None,
        comment: str | None = None,
        schema: str = "nkassist.evidence.decision.v1",
    ) -> dict[str, Any]:
        """
        Registra uma decisão do agente.

        sources:
          - lista de fontes/citações (ex: docs, trechos, ids, paths)
          - governança: você consegue provar de onde veio
        """
        payload = {
            "schema": schema,
            "type": "decision",
            "event_id": event_id,
            "ts": utc_now_iso(),
            "actor": actor or self.actor_default,
            "host": self.host,
            "risk_level": risk_level,
            "decision_engine": decision_engine,
            "confidence": confidence,
            "decision": decision,
            "sources": sources or [],
            "comment": comment,
        }
        return self._append(self.paths.decisions, payload)

    def log_approval(
        self,
        *,
        event_id: str,
        approved: bool,
        reviewed_by: str,
        review_comment: str | None = None,
        scope: str | None = None,
        schema: str = "nkassist.evidence.approval.v1",
    ) -> dict[str, Any]:
        """
        Registra uma aprovação humana (HITL).

        approved:
          - True: aprovado
          - False: rejeitado
        scope:
          - opcional, ex: "high_risk_action", "budget_change", "prod_change"
        """
        payload = {
            "schema": schema,
            "type": "approval",
            "event_id": event_id,
            "ts": utc_now_iso(),
            "reviewed_by": reviewed_by,
            "approved": approved,
            "scope": scope,
            "review_comment": review_comment,
        }
        return self._append(self.paths.approvals, payload)

    def log_action(
        self,
        *,
        event_id: str,
        action_type: str,
        target: str,
        status: Literal["planned", "executed", "failed", "skipped"] = "planned",
        details: dict[str, Any] | None = None,
        executed_by: str | None = None,
        schema: str = "nkassist.evidence.action.v1",
    ) -> dict[str, Any]:
        """
        Registra uma ação.
        Ex:
          - "create_ticket", "send_email", "update_budget_sheet", "apply_firewall_rule"
        target:
          - o alvo da ação (ex: "Jira", "ClickUp", "SophosXGS", "GDrive", "DB")
        """
        payload = {
            "schema": schema,
            "type": "action",
            "event_id": event_id,
            "ts": utc_now_iso(),
            "executed_by": executed_by or self.actor_default,
            "host": self.host,
            "action_type": action_type,
            "target": target,
            "status": status,
            "details": details or {},
        }
        return self._append(self.paths.actions, payload)
    
    def log_rag_query(
        self,
        *,
        event_id: str,
        query: str,
        top_k: int,
        results_count: int,
        results: list[dict[str, Any]] | None = None,
        pipeline: str = "faiss_retriever",
        actor: str | None = None,
        comment: str | None = None,
        schema: str = "nkassist.evidence.rag_query.v1",
    ) -> dict[str, Any]:
        """
        Registra uma consulta de retrieval do RAG.

        results:
          - lista resumida dos resultados retornados
          - ex: rank, chunk_id, source_path, title, score, start_char, end_char

        Benefício:
          - observabilidade de retrieval
          - auditoria de quais documentos/chunks estão sendo usados
          - base para métricas futuras (lacunas, score médio, docs mais recuperados)
        """
        payload = {
            "schema": schema,
            "type": "rag_query",
            "event_id": event_id,
            "ts": utc_now_iso(),
            "actor": actor or self.actor_default,
            "host": self.host,
            "query": query,
            "top_k": top_k,
            "results_count": results_count,
            "pipeline": pipeline,
            "results": results or [],
            "comment": comment,
        }
        return self._append(self.paths.rag_queries, payload)

    # ------------------------
    # Leitura (para filas HITL)
    # ------------------------

    def find_latest_approval(self, event_id: str) -> dict[str, Any] | None:
        """
        Busca a última aprovação para um event_id.
        Útil para: "posso executar?" / "está aprovado?"
        """
        path = self.paths.approvals
        if not path.exists():
            return None

        latest: dict[str, Any] | None = None
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("event_id") == event_id:
                    latest = obj
        return latest

    def is_approved(self, event_id: str) -> bool:
        """
        Retorna True se a última aprovação do evento for approved=True.
        """
        last = self.find_latest_approval(event_id)
        return bool(last and last.get("approved") is True)

    # ------------------------
    # Internals (append-only + hash-chain)
    # ------------------------

    def _append(self, file_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Adiciona 1 linha JSONL no arquivo.

        Se hash-chain estiver habilitado:
        - injeta prev_hash e line_hash
        - atualiza chain_state.json
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if self.enable_hash_chain:
            state = self._read_chain_state()
            prev_hash = state.get(str(file_path), None)
            payload["prev_hash"] = prev_hash

            # Calcula hash do payload sem o line_hash (pra não hash do próprio hash)
            canonical = _safe_json_dumps(payload)
            line_hash = _sha256_hex((prev_hash or "") + canonical)
            payload["line_hash"] = line_hash

            # Atualiza state para continuidade
            state[str(file_path)] = line_hash
            self._write_chain_state(state)

        # Escreve como JSONL (1 linha)
        with file_path.open("a", encoding="utf-8") as f:
            f.write(_safe_json_dumps(payload) + "\n")

        return payload

    def _read_chain_state(self) -> dict[str, str]:
        if not self.paths.chain_state.exists():
            return {}
        try:
            return json.loads(self.paths.chain_state.read_text(encoding="utf-8"))
        except Exception:
            # se o state corromper, recomeça — mas isso deve ser alertado em observabilidade depois
            return {}

    def _write_chain_state(self, state: dict[str, str]) -> None:
        self.paths.chain_state.write_text(_safe_json_dumps(state), encoding="utf-8")


# ------------------------
# Bootstrap helper
# ------------------------

def build_evidence_logger(evidence_dir: Path) -> EvidenceLog:
    """
    Cria EvidenceLog com configurações via env.

    Env vars úteis:
    - NKASSIST_EVIDENCE_HASH_CHAIN=true/false
    - NKASSIST_ACTOR_DEFAULT=eduardo (ou um service account)
    """
    enable_hash_chain = os.getenv("NKASSIST_EVIDENCE_HASH_CHAIN", "true").strip().lower() in (
        "1", "true", "yes", "y", "on"
    )
    actor_default = os.getenv("NKASSIST_ACTOR_DEFAULT", None)
    paths = build_evidence_paths(evidence_dir)
    return EvidenceLog(paths=paths, enable_hash_chain=enable_hash_chain, actor_default=actor_default)