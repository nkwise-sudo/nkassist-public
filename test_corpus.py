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
