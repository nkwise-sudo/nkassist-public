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
