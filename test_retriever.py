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
