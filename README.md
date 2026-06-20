# NKAssist

 Pipeline RAG profissional com recuperação semântica via FAISS, synthesis engine com validação em camadas e evidência auditável.
>
 ## Sobre este Repositório
Este repositório é a **versão pública de referência** do NKAssist.

O sistema completo — incluindo vault de conhecimento (LAGM), 
módulos proprietários de governança, pipelines de validação 
GxP e corpus regulatório — é mantido em repositório privado 
sob controle exclusivo da NKwise Consultoria.

O que está disponível aqui:
- Arquitetura e princípios de design do sistema
- Stack técnica e fluxo de conhecimento
- Módulo RAG (recuperação semântica via FAISS)
- Resultados de auditoria automatizada de qualidade

> Consultas sobre o sistema completo ou sobre projetos 
> de implementação: edunakahara@gmail.com

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FAISS](https://img.shields.io/badge/RAG-FAISS-blueviolet?style=flat-square)](https://github.com/facebookresearch/faiss)
[![LLM](https://img.shields.io/badge/LLM-Multi--Model-orange?style=flat-square)](https://platform.openai.com)
[![HITL](https://img.shields.io/badge/HITL-Human--in--the--Loop-green?style=flat-square)](https://github.com/nkwise-sudo/nkassist-public)
[![Audit](https://img.shields.io/badge/audit-13%2F13%20PASS-brightgreen?style=flat-square)](audits/audit_report_gxp_demo.json)

---

## Visão Geral

O **NKAssist** é um pipeline RAG (*Retrieval Augmented Generation*) construído para ambientes que exigem rastreabilidade, governança e qualidade verificável nas respostas geradas por IA.

O sistema recupera contexto relevante via índice FAISS antes de gerar qualquer resposta. Cada resposta passa por três camadas de validação — estrutural, heurística e semântica — antes de ser entregue. Toda operação é registrada em evidence logs imutáveis.

Este repositório inclui um **corpus de demonstração com 13 SOPs sintéticos** do domínio regulatório farmacêutico/biotech (GxP), com audit report público validando 13/13 queries com PASS.

---

## Pipeline

```
Query
  → Retriever (multi-query + rerank + diversity cap)
  → LLM → draft
  → Validator estrutural
  → Critic heurístico
  → Semantic Validator  (LLM separado, temperatura 0)
  → Final Answer
  → Evidence Log        (rag_queries.jsonl)
  → HITL               (se high-risk ou falha semântica)
```

---

## Estrutura do Projeto

```
nkassist-public/
├── .env.example                     ← variáveis de ambiente (template)
├── .gitignore
├── corpus/
│   └── gxp-demo/                    ← 13 SOPs sintéticos (corpus de demo)
│       ├── SOP-001-controle-temperatura-camaras-frias.md
│       ├── SOP-002-calibracao-balancas-analiticas.md
│       └── ...
├── rag/
│   ├── ingest.py                    ← ingestão e chunking de documentos
│   ├── vectorstore_faiss.py         ← build e query do índice FAISS
│   ├── retriever.py                 ← multi-query + rerank + diversity cap
│   ├── rerank.py                    ← reranking semântico
│   ├── focus.py                     ← context focusing
│   ├── parsers.py                   ← parsers de formato
│   └── synthesis_engine.py          ← validator + critic + semantic validator
├── core/
│   └── evidence.py                  ← evidence log estruturado
├── audits/
│   ├── run_gxp_audit.py             ← script de audit reproduzível
│   └── audit_report_gxp_demo.json  ← resultado validado: 13/13 PASS
├── data/                            ← gerado localmente (não versionado)
│   ├── corpus.jsonl
│   ├── faiss.index
│   └── faiss_meta.jsonl
└── evidence/                        ← logs gerados localmente (não versionados)
    └── rag_queries.jsonl
```

---

## Quick Start

### 1. Pré-requisitos

- Python 3.10+
- Chave OpenAI (`gpt-4o` e `text-embedding-3-large`)

```bash
pip install openai faiss-cpu numpy python-dotenv
```

### 2. Configurar ambiente

```bash
cp .env.example .env
# Editar .env com sua OPENAI_API_KEY
```

### 3. Ingestão do corpus

```bash
python test_ingest.py
# Esperado: 13 documentos, 92 chunks
```

### 4. Build do índice FAISS

```bash
python test_faiss.py
# Esperado: 92/92 chunks indexados, dim=3072
```

### 5. Testar retrieval

```bash
python test_retriever.py
# Esperado: SOP correto no #1 para cada query
```

### 6. Rodar audit

```bash
python audits/run_gxp_audit.py
# Esperado: 13/13 PASS
```

> Para o guia operacional completo com outputs validados, consulte [RUNBOOK.md](RUNBOOK.md).

---

## Corpus GxP Demo

13 SOPs sintéticos do domínio regulatório farmacêutico/biotech — nenhum dado real de paciente ou processo:

| SOP | Tema |
|-----|------|
| SOP-001 | Controle de Temperatura em Câmaras Frias |
| SOP-002 | Calibração de Balanças Analíticas |
| SOP-003 | Limpeza e Sanitização de Áreas Limpas |
| SOP-004 | Recebimento e Quarentena de Matéria-Prima |
| SOP-005 | Gestão de Desvios e Não-Conformidades |
| SOP-006 | Controle de Acesso a Áreas Classificadas |
| SOP-007 | Controle de Documentos e Registros |
| SOP-008 | Gestão de Fornecedores Críticos |
| SOP-009 | Coleta e Processamento de Amostras Biológicas |
| SOP-010 | Controle de Temperatura na Cadeia Fria |
| SOP-011 | Gestão de Resíduos Químicos e Biológicos |
| SOP-012 | Qualificação de Equipamentos Críticos (IQ/OQ/PQ) |
| SOP-013 | Controle de Mudanças |

O corpus pode ser substituído por qualquer conjunto de documentos `.md` ou `.txt` via `NKASSIST_KNOWLEDGE_DIR` no `.env`.

---

## Qualidade — Audit Report

Resultado validado em 2026-05-15 sobre o corpus GxP demo:

| Métrica | Resultado |
|---------|-----------|
| Queries testadas | 13 |
| PASS | 13 (100%) |
| FAIL | 0 |
| Score top-1 médio | 0.655 |
| Integridade do índice | 92/92 chunks |

Relatório completo: [`audits/audit_report_gxp_demo.json`](audits/audit_report_gxp_demo.json)

---

## Princípios de Design

| Princípio | Descrição |
|-----------|-----------|
| **Índice reconstruível** | O FAISS pode ser recriado do zero a qualquer momento a partir do corpus |
| **Validação em camadas** | Estrutural → Heurística → Semântica antes de cada resposta final |
| **Evidence logs** | Toda query, contexto e resposta registrados em append-only |
| **Human-in-the-Loop** | Aprovação humana antes de ações classificadas como high-risk |
| **Corpus plugável** | Qualquer diretório de documentos pode ser usado como fonte de conhecimento |
| **Audit reproduzível** | Script de audit incluído — qualquer pessoa pode validar a qualidade do retriever |

---

## Stack Técnica

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.10+ |
| Embeddings | text-embedding-3-large (OpenAI) |
| Indexação vetorial | FAISS |
| LLM | GPT-4o (configurável via env) |
| Paradigma | RAG — Retrieval Augmented Generation |
| Evidence log | JSON Lines (append-only) |

---

## Configuração

Todas as variáveis de configuração são gerenciadas via `.env`. Consulte [`.env.example`](.env.example) para a lista completa.

Principais variáveis:

```env
OPENAI_API_KEY=sk-...
NKASSIST_LLM_MODEL=gpt-4o-2024-08-06
NKASSIST_KNOWLEDGE_DIR=./corpus/gxp-demo
NKASSIST_DATA_DIR=./data
NKASSIST_CHUNK_SIZE=900
NKASSIST_CHUNK_OVERLAP=150
```

---

## Autor

**nkwise-sudo**  
Arquiteto de sistemas de IA — Especialista em governança e orquestração RAG/Multi-LLM em contextos regulatórios.  
[github.com/nkwise-sudo](https://github.com/nkwise-sudo)
