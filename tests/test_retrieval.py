from pathlib import Path

from incident_copilot.retrieval import BM25Retriever, HybridRetriever, load_runbooks, tokenize


ROOT = Path(__file__).resolve().parent.parent


def test_tokenize_normalizes_incident_terms():
    assert tokenize("P95 LATENCY: db.pool") == ["p95", "latency", "db.pool"]


def test_runbooks_are_chunked_by_section():
    chunks = load_runbooks(ROOT / "runbooks")
    assert len(chunks) >= 10
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


def test_bm25_returns_database_runbook_for_pool_timeout():
    chunks = load_runbooks(ROOT / "runbooks")
    results = BM25Retriever(chunks).search("connection pool timeout database", limit=3)
    assert results
    assert results[0].chunk.source == "database-saturation.md"


def test_hybrid_retrieval_expands_memory_terms():
    chunks = load_runbooks(ROOT / "runbooks")
    results = HybridRetriever(chunks).search("service memory problem", limit=4)
    assert any(result.chunk.source == "memory-pressure.md" for result in results)


def test_unknown_query_returns_no_results():
    chunks = load_runbooks(ROOT / "runbooks")
    assert BM25Retriever(chunks).search("zyxwv nonexistentphrase") == []

