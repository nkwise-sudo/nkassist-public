# rag/focus.py
"""
Context Focusing (V1)

Problema:
- Um chunk pode conter tópicos misturados (ex: "Corrige Cliente" + "Backup PDF").
- Jogar tudo no LLM aumenta ruído e derruba assertividade.

Solução:
- Extrair apenas as sentenças/linhas mais relevantes ao query.
- Critério: overlap de tokens (igual ao rerank) + bônus para termos do query.

Saída:
- snippet focado para prompt (não altera evidência, só melhora contexto).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag.rerank import tokenize_pt


def split_sentences(text: str) -> list[str]:
    """
    Split simples para português:
    - quebra por pontuação e por quebras de linha
    - mantém linhas úteis (checklists, caminhos, bullets)
    """
    # Primeiro quebra por linhas para capturar listas e paths
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    sentences: list[str] = []

    for ln in lines:
        # Se a linha é curta e parece item/bullet/path, mantém inteira
        if ln.startswith(("-", "•")) or "\\" in ln or ln.endswith(":"):
            sentences.append(ln)
            continue

        # Senão, quebra por fim de frase
        parts = re.split(r"(?<=[\.\!\?\;])\s+", ln)
        for p in parts:
            p = p.strip()
            if p:
                sentences.append(p)

    # Remove duplicatas preservando ordem
    seen = set()
    out = []
    for s in sentences:
        key = s.lower()
        if key not in seen:
            out.append(s)
            seen.add(key)
    return out


def sentence_score(query_tokens: set[str], sentence: str) -> float:
    """
    Score 0..1 baseado em overlap de tokens do query na sentença.
    """
    s_tokens = set(tokenize_pt(sentence))
    if not query_tokens:
        return 0.0
    hit = len(query_tokens.intersection(s_tokens))
    return hit / max(1, len(query_tokens))


def focus_text(query: str, chunk_text: str, *, max_sentences: int = 6) -> str:
    """
    Retorna um snippet focado (as N sentenças mais relevantes).
    """
    q_tokens = set(tokenize_pt(query))
    if not chunk_text.strip():
        return ""

    sentences = split_sentences(chunk_text)

    scored = []
    for s in sentences:
        sc = sentence_score(q_tokens, s)
        # bônus leve se contiver palavras "core" comuns em TI
        if any(k in s.lower() for k in ("backup", "restore", "drive", "pdf", "reposit", "cópia", "sincron")):
            sc += 0.05
        scored.append((sc, s))

    # pega top-N com score > 0 (senão pega as melhores mesmo)
    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = [s for sc, s in scored if sc > 0][:max_sentences]
    if not chosen:
        chosen = [s for sc, s in scored[:max_sentences]]

    return "\n".join(chosen).strip()