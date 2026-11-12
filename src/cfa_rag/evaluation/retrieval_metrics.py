"""Retrieval metrics: did the pages that support an answer appear among the top results?

A retrieved chunk is a (book, page range) span. It counts as a match when any page of a gold
source falls inside its range, in the same book.
"""

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

from cfa_rag.evaluation.golden import GoldenItem, PageRef, load_golden


@dataclass(frozen=True)
class RetrievedSpan:
    book: str
    page_start: int
    page_end: int


def _matches(span: RetrievedSpan, sources: Sequence[PageRef]) -> bool:
    return any(
        span.book == source.book
        and any(span.page_start <= page <= span.page_end for page in source.pages)
        for source in sources
    )


def hit_at_k(ranked: Sequence[RetrievedSpan], sources: Sequence[PageRef], k: int) -> float:
    """1.0 if any of the first k results matches a gold source, else 0.0."""
    return 1.0 if any(_matches(span, sources) for span in ranked[:k]) else 0.0


def reciprocal_rank_at_k(
    ranked: Sequence[RetrievedSpan], sources: Sequence[PageRef], k: int
) -> float:
    """1 / rank of the first matching result within the first k, else 0.0."""
    for rank, span in enumerate(ranked[:k], start=1):
        if _matches(span, sources):
            return 1 / rank
    return 0.0


def evaluate(
    results: Mapping[str, Sequence[RetrievedSpan]],
    golden: Sequence[GoldenItem],
    *,
    hit_k: int = 5,
    mrr_k: int = 10,
) -> dict[str, float]:
    """Mean hit@hit_k and MRR@mrr_k over the answerable items; a missing id counts as a miss."""
    items = [item for item in golden if item.kind == "answerable"]
    if not items:
        raise ValueError("no answerable items to evaluate")
    hits = [hit_at_k(results.get(i.id, []), i.sources, hit_k) for i in items]
    ranks = [reciprocal_rank_at_k(results.get(i.id, []), i.sources, mrr_k) for i in items]
    return {
        f"hit@{hit_k}": sum(hits) / len(items),
        f"mrr@{mrr_k}": sum(ranks) / len(items),
        "n": float(len(items)),
    }


class _Span(BaseModel):
    book: str
    page_start: int
    page_end: int


class _ResultLine(BaseModel):
    id: str
    ranked: list[_Span]


def load_results(path: Path) -> dict[str, list[RetrievedSpan]]:
    """Read JSON Lines of {"id", "ranked": [{"book", "page_start", "page_end"}]}."""
    results: dict[str, list[RetrievedSpan]] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = _ResultLine.model_validate_json(line)
        except ValidationError as error:
            raise ValueError(f"line {number}: {error.errors()[0]['msg']}") from error
        results[parsed.id] = [
            RetrievedSpan(s.book, s.page_start, s.page_end) for s in parsed.ranked
        ]
    return results


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cfa_rag.evaluation.retrieval_metrics", description=__doc__)
    ap.add_argument("--golden", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    args = ap.parse_args(argv)
    try:
        scores = evaluate(load_results(args.results), load_golden(args.golden))
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(scores))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
