import sys, os, json, time
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from rag.retriever import build_retriever_from_env

AUDIT_QUERIES = [
    {"id": "Q001", "category": "temperature_control",
     "query": "qual a faixa de temperatura e umidade para areas de producao farmaceutica",
     "expected_source": "SOP-001"},
    {"id": "Q002", "category": "calibration",
     "query": "qual a frequencia de calibracao de balancas analiticas",
     "expected_source": "SOP-002"},
    {"id": "Q003", "category": "cleaning",
     "query": "quais os produtos aprovados para sanitizacao de areas limpas",
     "expected_source": "SOP-003"},
    {"id": "Q004", "category": "receiving",
     "query": "quais os criterios de rejeicao no recebimento de materia-prima",
     "expected_source": "SOP-004"},
    {"id": "Q005", "category": "deviations",
     "query": "como classificar e registrar um desvio de qualidade",
     "expected_source": "SOP-005"},
    {"id": "Q006", "category": "access_control",
     "query": "quais os requisitos para acesso a areas limpas classificadas",
     "expected_source": "SOP-006"},
    {"id": "Q007", "category": "documentation",
     "query": "como controlar versoes de documentos regulatorios",
     "expected_source": "SOP-007"},
    {"id": "Q008", "category": "suppliers",
     "query": "como qualificar e monitorar fornecedores criticos",
     "expected_source": "SOP-008"},
    {"id": "Q009", "category": "biological_samples",
     "query": "qual o procedimento para coleta e processamento de amostras biologicas",
     "expected_source": "SOP-009"},
    {"id": "Q010", "category": "cold_chain",
     "query": "como monitorar temperatura na cadeia fria de produtos biologicos",
     "expected_source": "SOP-010"},
    {"id": "Q011", "category": "waste",
     "query": "como descartar residuos quimicos e biologicos de forma segura",
     "expected_source": "SOP-011"},
    {"id": "Q012", "category": "equipment_qualification",
     "query": "quais as etapas de qualificacao IQ OQ PQ para equipamentos criticos",
     "expected_source": "SOP-012"},
    {"id": "Q013", "category": "change_control",
     "query": "qual o processo de avaliacao e aprovacao de mudancas no sistema de qualidade",
     "expected_source": "SOP-013"},
]

def run_audit():
    retriever = build_retriever_from_env(Path("."))
    results = []
    passed = 0

    print(f"Iniciando audit - {len(AUDIT_QUERIES)} queries\n")

    for q in AUDIT_QUERIES:
        t0 = time.time()
        pack = retriever.retrieve(q["query"])
        elapsed_ms = round((time.time() - t0) * 1000, 2)

        top_sources = [r.source_path for r in pack.raw_results[:3]]
        top_scores  = [round(r.score, 4) for r in pack.raw_results[:3]]
        hit = any(q["expected_source"].lower() in s.lower() for s in top_sources)
        status = "PASS" if hit else "FAIL"
        if hit:
            passed += 1

        results.append({
            "id": q["id"],
            "category": q["category"],
            "query": q["query"],
            "expected_source": q["expected_source"],
            "status": status,
            "top_3_sources": top_sources,
            "top_3_scores": top_scores,
            "hit_in_top3": hit,
            "retrieval_time_ms": elapsed_ms,
        })

        icon = "PASS" if hit else "FAIL"
        print(f"[{icon}] {q['id']} - {q['query'][:55]}...")
        if not hit:
            print(f"       Esperado : {q['expected_source']}")
            print(f"       Top-3    : {top_sources}")

    total = len(AUDIT_QUERIES)
    coverage = passed / total
    overall = "PASS" if coverage == 1.0 else "WARNING" if coverage >= 0.7 else "FAIL"

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "corpus": "gxp-demo",
        "overall_status": overall,
        "summary": {
            "total_queries": total,
            "passed": passed,
            "failed": total - passed,
            "coverage": round(coverage, 4),
        },
        "queries": results,
    }

    output_path = Path("audits/audit_report_gxp_demo.json")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*55}")
    print(f"RESULTADO FINAL")
    print(f"{'='*55}")
    print(f"Status   : {overall}")
    print(f"PASS     : {passed}/{total} ({coverage*100:.1f}%)")
    print(f"Relatorio: {output_path}")

if __name__ == "__main__":
    run_audit()