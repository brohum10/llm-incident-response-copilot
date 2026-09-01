from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from .models import RetrievedChunk, RunbookChunk


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.-]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def load_runbooks(directory: Path) -> list[RunbookChunk]:
    chunks: list[RunbookChunk] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        sections = re.split(r"(?m)^##\s+", text)
        document_title = sections[0].lstrip("# ").strip() or path.stem
        for index, section in enumerate(sections[1:] or [text]):
            lines = section.strip().splitlines()
            title = lines[0].strip() if lines else document_title
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else section.strip()
            if body:
                chunks.append(
                    RunbookChunk(
                        chunk_id=f"{path.stem}:{index + 1}",
                        source=path.name,
                        title=title,
                        text=body,
                        tags=tuple(tokenize(document_title)),
                    )
                )
    return chunks


class BM25Retriever:
    def __init__(self, chunks: list[RunbookChunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self._tokens = [tokenize(f"{c.title} {' '.join(c.tags)} {c.text}") for c in chunks]
        self._term_frequencies = [Counter(tokens) for tokens in self._tokens]
        self._document_frequency: Counter[str] = Counter()
        for tokens in self._tokens:
            self._document_frequency.update(set(tokens))
        self._avg_length = sum(map(len, self._tokens)) / max(1, len(self._tokens))

    def search(self, query: str, limit: int = 4) -> list[RetrievedChunk]:
        query_terms = Counter(tokenize(query))
        scored: list[RetrievedChunk] = []
        total_documents = len(self.chunks)
        for index, chunk in enumerate(self.chunks):
            score = 0.0
            document_length = len(self._tokens[index])
            for term, query_count in query_terms.items():
                frequency = self._term_frequencies[index].get(term, 0)
                if not frequency:
                    continue
                document_frequency = self._document_frequency[term]
                inverse_frequency = math.log(1 + (total_documents - document_frequency + 0.5) / (document_frequency + 0.5))
                normalizer = frequency + self.k1 * (1 - self.b + self.b * document_length / max(1, self._avg_length))
                score += query_count * inverse_frequency * frequency * (self.k1 + 1) / normalizer
            if score > 0:
                scored.append(RetrievedChunk(chunk=chunk, score=round(score, 6)))
        return sorted(scored, key=lambda result: (-result.score, result.chunk.chunk_id))[:limit]


class HybridRetriever:
    """Combines BM25 with a small incident-domain synonym expansion layer."""

    _synonyms = {
        "latency": "slow timeout p95 response time",
        "database": "postgres sql connection pool lock query",
        "errors": "exceptions failures 5xx error rate",
        "memory": "oom heap garbage collection allocation",
        "traffic": "requests load rate throughput",
    }

    def __init__(self, chunks: list[RunbookChunk]):
        self.bm25 = BM25Retriever(chunks)

    def search(self, query: str, limit: int = 4) -> list[RetrievedChunk]:
        lowered = query.lower()
        expansion = " ".join(value for key, value in self._synonyms.items() if key in lowered)
        return self.bm25.search(f"{query} {expansion}", limit=limit)

