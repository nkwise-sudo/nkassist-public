# NKAssist

> Assistente profissional com IA baseado em RAG (Retrieval Augmented Generation) com recuperação semântica via FAISS e pipeline de conhecimento versionado.

![Python](https://img.shields.io/badge/Python-87.9%25-3776AB?style=flat-square&logo=python&logoColor=white)
![Shell](https://img.shields.io/badge/Shell-8.5%25-4EAA25?style=flat-square&logo=gnu-bash&logoColor=white)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=flat-square)
![RAG](https://img.shields.io/badge/RAG-FAISS-blueviolet?style=flat-square)
![LLM](https://img.shields.io/badge/LLM-Multi--Model-orange?style=flat-square)
![HITL](https://img.shields.io/badge/HITL-Human--in--the--Loop-green?style=flat-square)

---

## Visão Geral

O **NKAssist** é um assistente de IA profissional que utiliza um vault de conhecimento versionado como fonte única da verdade (*source of truth*). O sistema recupera contexto relevante via índice FAISS antes de gerar respostas, garantindo precisão, rastreabilidade e controle total sobre o conhecimento utilizado.

O projeto foi construído com foco em **governança desde o design** — cada resposta é rastreável, cada fonte é citada, e nenhuma informação entra no sistema sem passar pelo pipeline oficial de ingest.

---

## Arquitetura

```
/srv
├── lagm-vault          → vault oficial de conhecimento (Obsidian + Git)
├── nkassist            → assistente com RAG + FAISS
├── ops-classifier      → motor de classificação operacional
└── nkwise/
    └── shared/scripts  → scripts operacionais compartilhados
```

O NKAssist **não** mantém cópia local do conhecimento. Ele lê diretamente do vault via variável de ambiente:

```env
NKASSIST_KNOWLEDGE_DIR=/srv/lagm-vault
```

---

## Fluxo de Conhecimento

```
Obsidian (edição)
     ↓
  GitHub (versionamento)
     ↓
  git pull → /srv/lagm-vault
     ↓
  RAG ingest
     ↓
  FAISS rebuild
     ↓
  NKAssist (resposta contextualizada)
```

---

## Pipeline de Atualização

O script oficial gerencia todo o ciclo de atualização:

```bash
/srv/nkwise/shared/scripts/update_vault.sh
```

Etapas executadas:
1. `git pull` no vault (`/srv/lagm-vault`)
2. Ingest do RAG com os novos documentos
3. Rebuild do índice vetorial FAISS

---

## Estrutura do Projeto

```
nkassist/
├── rag/        → ingest, indexação e retrieval semântico
├── core/       → configurações e inicialização do sistema
├── agent/      → lógica do assistente e orquestração
├── data/       → configurações do corpus e índices
├── lab/        → experimentos e protótipos
├── lab_ui/     → interface de laboratório
├── audits/     → relatórios de qualidade RAG
├── docs/       → documentação técnica
└── ops/        → scripts operacionais
```

---

## Princípios de Design

| Princípio | Descrição |
|---|---|
| **Vault único** | Única fonte de verdade — sem duplicação de conhecimento |
| **Ingest controlado** | Nenhum documento entra no índice sem passar pelo pipeline oficial |
| **Índice reconstruível** | O FAISS pode ser recriado do zero a qualquer momento a partir do vault |
| **Logs append-only** | Rastreabilidade completa de operações sem sobrescrita |
| **Human-in-the-Loop** | Aprovação humana antes de ações críticas |
| **Citations required** | Toda resposta exige citação da fonte no vault |

---

## Stack Técnica

```yaml
Linguagem principal: Python 3.x
Recuperação semântica: FAISS
Paradigma: RAG (Retrieval Augmented Generation)
LLM: Multi-model (OpenAI GPT-4.1, configurável via env)
Embeddings: text-embedding-3-large (OpenAI)
Vault de conhecimento: Obsidian + Git
Scripts operacionais: Shell / Bash
Infraestrutura: Linux Server
```

---

## Qualidade — Audit Report

O sistema possui módulo de auditoria automatizada que valida a qualidade das respostas:

| Métrica | Resultado |
|---|---|
| Total de queries testadas | 38 |
| PASS | 38 (100%) |
| WARNING | 0 |
| FAIL | 0 |
| Score médio | 10.0 |
| Coverage média | 1.0 |

---

## Autor

**nkwise-sudo**
Arquiteto de sistemas de IA — Consultor em governança e orquestração Multi-LLM
[github.com/nkwise-sudo](https://github.com/nkwise-sudo)
