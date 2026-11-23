# test_integrity.py
from pathlib import Path

corpus_path = Path("data/corpus.jsonl")
meta_path   = Path("data/faiss_meta.jsonl")

corpus_count = sum(1 for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip())
meta_count   = sum(1 for line in meta_path.read_text(encoding="utf-8").splitlines() if line.strip())

print(f"Corpus  : {corpus_count} chunks")
print(f"Meta    : {meta_count} chunks")
print(f"Match   : {'OK' if corpus_count == meta_count else 'FALHA - corpus e meta divergem!'}")
