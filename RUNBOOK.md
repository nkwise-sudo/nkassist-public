# NKAssist — GxP Demo Runbook
**Versão:** 1.1
**Data:** 2026-05-15
**Propósito:** Guia operacional para rodar, testar e validar o NKAssist sobre o corpus GxP demo.

> **v1.1 — Correções validadas em testes reais:**
> - Chave FAISS corrigida: `corpus_rows` (não `indexed`)
> - Import do synthesis_engine corrigido: `from rag.synthesis_engine import`
> - Queries do audit sem acentos (compatibilidade PowerShell/Windows)
> - Chunks esperados ajustados para 92 (resultado real dos 13 SOPs)
> - Scripts salvos em arquivo `.py` em vez de `-c` inline (evita erros de parsing no PowerShell)

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Configuração do Ambiente](#3-configuração-do-ambiente)
4. [Fase 1 — Ingestão do Corpus](#4-fase-1--ingestão-do-corpus)
5. [Fase 2 — Build do Índice FAISS](#5-fase-2--build-do-índice-faiss)
6. [Fase 3 — Validação do Retriever](#6-fase-3--validação-do-retriever)
7. [Fase 4 — Teste do Synthesis Engine](#7-fase-4--teste-do-synthesis-engine)
8. [Fase 5 — Audit Report](#8-fase-5--audit-report)
9. [Resultados Esperados](#9-resultados-esperados)
10. [Checklist de Publicação](#10-checklist-de-publicação)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Pré-requisitos

### Ambiente Python

```bash
# Verificar versão (requerido: 3.10+)
python --version
# Retorno esperado: Python 3.10.x ou superior

# Verificar dependências instaladas
pip list | findstr -i "openai faiss numpy python-dotenv"
# Retorno esperado (exemplo):
# faiss-cpu        1.7.4
# numpy            1.26.x
# openai           1.x.x
# python-dotenv    1.0.x
```

> **Nota Windows/PowerShell:** Todos os scripts deste runbook devem ser salvos em
> arquivos `.py` e executados com `python script.py`. Blocos inline com `-c` causam
> erros de parsing no PowerShell quando contêm aspas duplas ou strings multilinha.

### Variáveis de Ambiente

O arquivo `.env` deve existir na raiz do projeto.

```bash
# Windows — verificar se .env existe
dir .env
# Retorno esperado: arquivo listado com data e tamanho
```

### Chave OpenAI

Salve como `test_api.py` e execute:

```python
# test_api.py
import openai, os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
resp = client.models.list()
print('API OK - modelos disponiveis:', len(list(resp)))
```

```bash
python test_api.py
# Retorno esperado: API OK - modelos disponiveis: N
# Retorno de erro: AuthenticationError → verificar OPENAI_API_KEY no .env
```

---

## 2. Estrutura de Diretórios

Estrutura esperada após testes completos:

```
nkassist-public/
├── .env                          ← variáveis de ambiente (NÃO vai ao GitHub)
├── .env.example                  ← template público (vai ao GitHub)
├── .gitignore                    ← exclui .env, data/, evidence/
├── LICENSE                       ← licença do repositório
├── corpus/
│   └── gxp-demo/                 ← 13 SOPs (vai ao GitHub)
│       ├── SOP-001-controle-temperatura-camaras-frias.md
│       ├── SOP-002-calibracao-balancas-analiticas.md
│       └── ... (13 arquivos total)
├── rag/
│   ├── __init__.py
│   ├── ingest.py
│   ├── retriever.py
│   ├── rerank.py
│   ├── focus.py
│   ├── parsers.py
│   ├── vectorstore_faiss.py
│   └── synthesis_engine.py
├── core/
│   ├── __init__.py
│   └── evidence.py
├── data/
│   ├── .gitkeep                  ← pasta versionada, conteúdo ignorado
│   ├── corpus.jsonl              ← gerado pelo ingest (NÃO vai ao GitHub)
│   ├── faiss.index               ← gerado pelo FAISS (NÃO vai ao GitHub)
│   └── faiss_meta.jsonl          ← gerado pelo FAISS (NÃO vai ao GitHub)
├── evidence/
│   ├── .gitkeep
│   └── rag_queries.jsonl         ← logs (NÃO vai ao GitHub)
└── audits/
    ├── __init__.py
    ├── run_gxp_audit.py
    └── audit_report_gxp_demo.json  ← resultado validado (vai ao GitHub)
```

---

## 3. Configuração do Ambiente

### .env para Demo GxP

Copie `.env.example` para `.env` e preencha:

```env
# LLM
OPENAI_API_KEY=sk-...
NKASSIST_LLM_MODEL=gpt-4o-2024-08-06

# Paths — corpus GxP demo
NKASSIST_KNOWLEDGE_DIR=./corpus/gxp-demo
NKASSIST_DATA_DIR=./data
NKASSIST_EVIDENCE_DIR=./evidence

# Ingest
NKASSIST_ALLOWED_EXT=.md,.txt
NKASSIST_CHUNK_SIZE=900
NKASSIST_CHUNK_OVERLAP=150
NKASSIST_EXCLUDED_DIRS=archive,.git

# Retriever
NKASSIST_MAX_SOURCES=6
NKASSIST_MAX_PER_DOC=2
NKASSIST_RECALL_MULT=4
NKASSIST_FOCUS_MAX_SENTENCES=10
NKASSIST_REQUIRE_CITATIONS=true

# Pipeline flags
NKASSIST_MULTI_QUERY=true
NKASSIST_RERANK=true
NKASSIST_OBSIDIAN_GRAPH_BONUS=false
NKASSIST_DIVERSITY_CAP=true
```

> **`NKASSIST_OBSIDIAN_GRAPH_BONUS=false`** — os SOPs não têm wikilinks Obsidian.
> Graph bonus é feature do sistema LAGM interno, não do corpus GxP demo.

### Criar diretórios de saída

```bash
# Windows
mkdir data
mkdir evidence
mkdir audits
```

---

## 4. Fase 1 — Ingestão do Corpus

Salve como `test_ingest.py` e execute:

```python
# test_ingest.py
from pathlib import Path
from rag.ingest import build_ingestor_from_env

ingestor = build_ingestor_from_env(Path("."))
result = ingestor.ingest()

print("=== RESULTADO DA INGESTÃO ===")
print("Documentos processados :", result["documents"])
print("Chunks gerados         :", result["chunks_written"])
print("Corpus salvo em        :", result["corpus_path"])
print("Extensoes aceitas      :", result["allowed_ext"])
print("Chunk size             :", result["chunk_size"])
print("Overlap                :", result["overlap"])
```

```bash
python test_ingest.py
```

**Retorno esperado:**
```
=== RESULTADO DA INGESTÃO ===
Documentos processados : 13
Chunks gerados         : 92
Corpus salvo em        : data\corpus.jsonl
Extensoes aceitas      : ['.md', '.txt']
Chunk size             : 900
Overlap                : 150
```

> **Se `Documentos processados` for menor que 13:** verificar se `NKASSIST_KNOWLEDGE_DIR`
> aponta para `./corpus/gxp-demo` e não para outro vault.

### Validar corpus gerado

Salve como `test_corpus.py` e execute:

```python
# test_corpus.py
import json
from pathlib import Path
from collections import Counter

corpus_path = Path("data/corpus.jsonl")
chunks = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines()]

print(f"Total de chunks: {len(chunks)}")
print()
print("Chunks por documento:")
counter = Counter(c["source_path"] for c in chunks)
for doc, count in sorted(counter.items()):
    print(f"  {count:3d}  {doc}")
```

```bash
python test_corpus.py
```

**Retorno esperado:**
```
Total de chunks: 92

Chunks por documento:
    6  SOP-001-controle-temperatura-camaras-frias.md
    6  SOP-002-calibracao-balancas-analiticas.md
    5  SOP-003-limpeza-sanitizacao-areas-limpas.md
    5  SOP-004-recebimento-quarentena-materia-prima.md
    5  SOP-005-gestao-desvios-nao-conformidades.md
    4  SOP-006-controle-acesso-areas-classificadas.md
    5  SOP-007-controle-documentos-registros.md
    4  SOP-008-gestao-fornecedores-criticos.md
    7  SOP-009-coleta-processamento-amostras-biologicas.md
   10  SOP-010-controle-temperatura-cadeia-fria.md
   12  SOP-011-gestao-residuos-quimicos-biologicos.md
   13  SOP-012-qualificacao-equipamentos-criticos.md
   10  SOP-013-controle-mudancas.md
```

> **Todos os 13 SOPs devem aparecer.** Variações de ±1 chunk por documento são normais
> em re-execuções — o chunking é determinístico, mas depende do conteúdo exato do arquivo.

---

## 5. Fase 2 — Build do Índice FAISS

Salve como `test_faiss.py` e execute:

```python
# test_faiss.py
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from rag.vectorstore_faiss import build_faiss_store_from_env

store = build_faiss_store_from_env(Path("."))
corpus_path = Path(os.getenv("NKASSIST_DATA_DIR", "data")) / "corpus.jsonl"
summary = store.build_from_corpus(corpus_path)

print("=== BUILD FAISS ===")
print("Chunks indexados :", summary["corpus_rows"])   # chave correta: corpus_rows
print("Dimensao         :", summary["dim"])
print("Modelo embedding :", summary["embed_model"])
print("Indice salvo em  :", summary["index_path"])
print("Meta salvo em    :", summary["meta_path"])
```

```bash
python test_faiss.py
```

**Retorno esperado:**
```
=== BUILD FAISS ===
Chunks indexados : 92
Dimensao         : 3072
Modelo embedding : text-embedding-3-large
Indice salvo em  : data\faiss.index
Meta salvo em    : data\faiss_meta.jsonl
```

> **CRÍTICO:** `Chunks indexados` deve ser **igual** ao `Chunks gerados` na Fase 1 (92).
> Se for menor, há perda no build — não avançar antes de investigar.

### Verificar integridade

```python
# test_integrity.py
from pathlib import Path

corpus_path = Path("data/corpus.jsonl")
meta_path   = Path("data/faiss_meta.jsonl")

corpus_count = sum(1 for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip())
meta_count   = sum(1 for line in meta_path.read_text(encoding="utf-8").splitlines() if line.strip())

print(f"Corpus  : {corpus_count} chunks")
print(f"Meta    : {meta_count} chunks")
print(f"Match   : {'OK' if corpus_count == meta_count else 'FALHA - corpus e meta divergem!'}")
```

```bash
python test_integrity.py
```

**Retorno esperado:**
```
Corpus  : 92 chunks
Meta    : 92 chunks
Match   : OK
```

---

## 6. Fase 3 — Validação do Retriever

Salve como `test_retriever.py` e execute:

```python
# test_retriever.py
import sys
sys.path.insert(0, ".")
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from rag.retriever import build_retriever_from_env

retriever = build_retriever_from_env(Path("."))

queries = [
    "qual a temperatura correta para armazenamento de amostras biologicas",
    "como realizar a calibracao de balancas analiticas",
    "quais os criterios de rejeicao de materia-prima",
    "como registrar um desvio de qualidade",
    "procedimento de limpeza de areas produtivas",
]

for query in queries:
    pack = retriever.retrieve(query)
    print(f"\nQuery: {query}")
    print(f"Chunks recuperados: {len(pack.raw_results)}")
    for i, r in enumerate(pack.raw_results[:3], 1):
        print(f"  #{i} score={r.score:.4f} | {r.source_path}")
```

```bash
python test_retriever.py
```

**Retorno esperado (validado):**
```
Query: qual a temperatura correta para armazenamento de amostras biologicas
Chunks recuperados: 6
  #1 score=0.6515 | SOP-009-coleta-processamento-amostras-biologicas.md
  #2 score=0.6469 | SOP-010-controle-temperatura-cadeia-fria.md
  #3 score=0.6227 | SOP-001-controle-temperatura-camaras-frias.md

Query: como realizar a calibracao de balancas analiticas
Chunks recuperados: 6
  #1 score=0.6730 | SOP-002-calibracao-balancas-analiticas.md
  #2 score=0.6060 | SOP-002-calibracao-balancas-analiticas.md
  #3 score=0.6032 | SOP-010-controle-temperatura-cadeia-fria.md

Query: quais os criterios de rejeicao de materia-prima
Chunks recuperados: 6
  #1 score=0.6363 | SOP-004-recebimento-quarentena-materia-prima.md
  #2 score=0.6193 | SOP-008-gestao-fornecedores-criticos.md
  #3 score=0.6055 | SOP-013-controle-mudancas.md

Query: como registrar um desvio de qualidade
Chunks recuperados: 6
  #1 score=0.6492 | SOP-005-gestao-desvios-nao-conformidades.md
  #2 score=0.6313 | SOP-010-controle-temperatura-cadeia-fria.md
  #3 score=0.6305 | SOP-013-controle-mudancas.md

Query: procedimento de limpeza de areas produtivas
Chunks recuperados: 6
  #1 score=0.6664 | SOP-003-limpeza-sanitizacao-areas-limpas.md
  #2 score=0.6352 | SOP-006-controle-acesso-areas-classificadas.md
  #3 score=0.6221 | SOP-012-qualificacao-equipamentos-criticos.md
```

> **Sinal verde:** SOP correto no #1 para todas as queries (5/5 validado).
> **Nota:** SOP-002 aparece duas vezes no top-2 da segunda query — comportamento esperado
> com `MAX_PER_DOC=2`. O diversity cap está funcionando corretamente.

---

## 7. Fase 4 — Teste do Synthesis Engine

> **Import correto:** `from rag.synthesis_engine import` — o módulo está em `rag/`, não na raiz.

Salve como `test_synthesis.py` e execute:

```python
# test_synthesis.py
import sys
sys.path.insert(0, ".")
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from rag.retriever import build_retriever_from_env
from rag.synthesis_engine import run_synthesis_pipeline

retriever = build_retriever_from_env(Path("."))

query = "como registrar um desvio de qualidade no processo produtivo"
pack  = retriever.retrieve(query)

result = run_synthesis_pipeline(
    query=query,
    raw_results=pack.raw_results,
)

print("=== SYNTHESIS RESULT ===")
print("Validator status :", result.validator_status)
print("Critic status    :", result.critic_status)
print("Used fallback    :", result.used_fallback)
print("Critic notes     :", result.critic_notes)
print()
print("--- Final Answer (preview) ---")
print(result.final_answer[:400])
print()
print("--- Evidence Log ---")
ev = result.evidence_log
print("Chunks recuperados :", ev["retrieval_summary"]["retrieved_chunks_count"])
print("Coverage ratio     :", ev["validation_summary"]["coverage_ratio"])
print("Claims geradas     :", len(ev["claims"]))
```

```bash
python test_synthesis.py
```

**Retorno esperado (validado):**
```
=== SYNTHESIS RESULT ===
Validator status : ok
Critic status    : ok
Used fallback    : False
Critic notes     : ['critic_v0_no_major_issues']

--- Final Answer (preview) ---
Resposta baseada no contexto recuperado para: como registrar um desvio de qualidade...
[conteudo do SOP-005]

--- Evidence Log ---
Chunks recuperados : 6
Coverage ratio     : 0.5
Claims geradas     : 1
```

> **Coverage ratio 0.5** é esperado para o pipeline sem LLM (draft heurístico).
> Com `run_synthesis_with_draft` + LLM externo, coverage sobe para 0.8+.

---

## 8. Fase 5 — Audit Report

O script `audits/run_gxp_audit.py` está incluído no repositório. Execute diretamente:

```bash
python audits/run_gxp_audit.py
```

**Retorno esperado (validado em 2026-05-15):**
```
Iniciando audit - 13 queries

[PASS] Q001 - qual a faixa de temperatura e umidade para areas de pro...
[PASS] Q002 - qual a frequencia de calibracao de balancas analiticas...
[PASS] Q003 - quais os produtos aprovados para sanitizacao de areas l...
[PASS] Q004 - quais os criterios de rejeicao no recebimento de materi...
[PASS] Q005 - como classificar e registrar um desvio de qualidade...
[PASS] Q006 - quais os requisitos para acesso a areas limpas classifi...
[PASS] Q007 - como controlar versoes de documentos regulatorios...
[PASS] Q008 - como qualificar e monitorar fornecedores criticos...
[PASS] Q009 - qual o procedimento para coleta e processamento de amos...
[PASS] Q010 - como monitorar temperatura na cadeia fria de produtos b...
[PASS] Q011 - como descartar residuos quimicos e biologicos de forma ...
[PASS] Q012 - quais as etapas de qualificacao IQ OQ PQ para equipamen...
[PASS] Q013 - qual o processo de avaliacao e aprovacao de mudancas no...

=======================================================
RESULTADO FINAL
=======================================================
Status   : PASS
PASS     : 13/13 (100.0%)
Relatorio: audits\audit_report_gxp_demo.json
```

> **Se algum FAIL aparecer:** o retriever não está encontrando o SOP correto.
> Verifique se o `.env` aponta para `./corpus/gxp-demo` e se o FAISS foi rebuilt
> após a última ingestão.

---

## 9. Resultados Esperados

### Métricas de referência (validadas)

| Métrica | Valor Validado | Mínimo Aceitável |
|---|---|---|
| Documentos ingeridos | 13/13 | 13/13 |
| Chunks gerados | 92 | 85+ |
| Chunks indexados FAISS | 92/92 | corpus == faiss |
| Queries PASS no audit | 13/13 (100%) | 10/13 (77%) |
| Score top-1 médio | 0.65 | 0.55+ |
| Validator status | ok | ok |
| Critic status | ok | ok |

### Sinais de qualidade do retriever

**Bom:**
- SOP correto no #1 para query direta sobre aquele SOP
- Score top-1 > 0.60 para queries específicas
- SOPs de temperatura agrupados (SOP-001 + SOP-009 + SOP-010)

**Com problema:**
- Score top-1 < 0.45 — corpus mal chunkado ou query fora do domínio
- Mesmo SOP em todas as posições — diversity cap com problema
- `Chunks recuperados: 0` — índice FAISS corrompido ou vazio

---

## 10. Checklist de Publicação

```
INGESTÃO
[x] 13 documentos processados
[x] corpus.jsonl gerado em data/
[x] Todos os 13 SOPs com chunks > 0

BUILD FAISS
[x] corpus_rows == chunks_gerados (92 == 92)
[x] faiss.index presente em data/
[x] faiss_meta.jsonl com mesmo número de linhas do corpus

RETRIEVER
[x] 5 queries retornam SOP correto no #1
[x] Score top-1 > 0.60 em todas as queries
[x] Diversity cap funcionando

SYNTHESIS
[x] validator_status = ok
[x] critic_status = ok
[x] used_fallback = False

AUDIT
[x] audit_report_gxp_demo.json gerado
[x] Status: PASS
[x] 13/13 queries PASS

SEGURANÇA
[x] .env NÃO está no repositório
[x] .env.example presente sem valores reais
[x] .gitignore cobre: .env, data/, evidence/, *.jsonl, *.index
[x] Nenhuma chave API no código
[x] SOPs são todos sintéticos (nenhum dado real de paciente ou processo)
```

---

## 11. Troubleshooting

### `ModuleNotFoundError: No module named 'rag'`

```bash
# Garantir que está na raiz do projeto
cd F:\projects\claude\nkassist-public
# Adicionar ao PYTHONPATH se necessário
$env:PYTHONPATH = "F:\projects\claude\nkassist-public"
```

### `KeyError: 'indexed'` no build FAISS

```
# Chave correta é corpus_rows, não indexed
# Usar: summary["corpus_rows"]
```

### `ModuleNotFoundError: No module named 'synthesis_engine'`

```
# Import correto:
from rag.synthesis_engine import run_synthesis_pipeline
# NÃO:
from synthesis_engine import run_synthesis_pipeline
```

### `FileNotFoundError: corpus.jsonl not found`

```python
# test_env.py
import os
from dotenv import load_dotenv
load_dotenv()
print("DATA_DIR      :", os.getenv("NKASSIST_DATA_DIR"))
print("KNOWLEDGE_DIR :", os.getenv("NKASSIST_KNOWLEDGE_DIR"))
```

### `AuthenticationError` na API OpenAI

```python
# test_key.py
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("OPENAI_API_KEY", "")
print("Chave presente:", bool(key))
print("Prefixo:", key[:7] + "..." if key else "AUSENTE")
```

### FAISS com menos chunks que corpus

```python
# test_integrity.py
from pathlib import Path
corpus = list(Path("data/corpus.jsonl").open(encoding="utf-8"))
meta   = list(Path("data/faiss_meta.jsonl").open(encoding="utf-8"))
print(f"Corpus : {len(corpus)} linhas")
print(f"Meta   : {len(meta)} linhas")
if len(corpus) != len(meta):
    print("DIVERGENCIA - reconstruir indice FAISS")
else:
    print("OK - indice integro")
```

### Queries retornando FAIL no audit

Verifique se o `.env` está apontando para o corpus GxP e não para outro vault:

```bash
# Windows
Get-Content .env | Select-String "KNOWLEDGE_DIR"
# Retorno esperado:
# NKASSIST_KNOWLEDGE_DIR=./corpus/gxp-demo
```

---

## Referências Rápidas

| Componente | Arquivo | Função principal |
|---|---|---|
| Ingestão | `rag/ingest.py` | `build_ingestor_from_env()` → `.ingest()` |
| Vector store | `rag/vectorstore_faiss.py` | `build_faiss_store_from_env()` → `.build_from_corpus()` |
| Retriever | `rag/retriever.py` | `build_retriever_from_env()` → `.retrieve(query)` |
| Synthesis | `rag/synthesis_engine.py` | `run_synthesis_pipeline()` |
| Audit | `audits/run_gxp_audit.py` | `python audits/run_gxp_audit.py` |

---

## Histórico de Versões

### v1.1 — 2026-05-15
- Corrigida chave FAISS: `corpus_rows` (era `indexed`)
- Corrigido import: `from rag.synthesis_engine import` (era `from synthesis_engine import`)
- Queries do audit sem acentos (compatibilidade Windows/PowerShell)
- Chunks esperados ajustados para 92 (resultado real validado)
- Scripts migrados para arquivos `.py` (evita erros de parsing no PowerShell)
- Checklist de publicação marcado com resultados reais
- Retornos esperados substituídos por outputs reais dos testes

### v1.0 — 2026-05-15
- Versão inicial

---

*NKAssist GxP Demo Runbook v1.1 — validado em 2026-05-15*
