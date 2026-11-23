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
