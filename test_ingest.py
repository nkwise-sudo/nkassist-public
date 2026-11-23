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
