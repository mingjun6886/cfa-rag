import json
from pathlib import Path

import pytest

from cfa_rag.evaluation.golden import GoldenItem, PageRef
from cfa_rag.evaluation.retrieval_metrics import (
    RetrievedSpan,
    evaluate,
    hit_at_k,
    main,
    reciprocal_rank_at_k,
)

GOLD = [PageRef(book="B1", pages=[30, 31])]
MISS, HIT = RetrievedSpan("B1", 1, 2), RetrievedSpan("B1", 31, 33)


def _answerable(item_id: str) -> GoldenItem:
    return GoldenItem(
        id=item_id, question="q?", language="en", kind="answerable",
        reference_answer="a", sources=GOLD,
    )  # fmt: skip


UNANSWERABLE_Q3 = GoldenItem(id="q3", question="q?", language="en", kind="unanswerable")


def test_multi_page_chunk_counts_when_any_gold_page_is_inside() -> None:
    assert hit_at_k([RetrievedSpan("B1", 28, 30)], GOLD, 5) == 1.0
    assert hit_at_k([RetrievedSpan("B2", 30, 30)], GOLD, 5) == 0.0  # same pages, other book
    assert hit_at_k([RetrievedSpan("B1", 32, 40)], GOLD, 5) == 0.0  # next to the gold pages


def test_hit_respects_k_and_short_lists() -> None:
    assert hit_at_k([MISS, MISS, HIT], GOLD, 3) == 1.0
    assert hit_at_k([MISS, MISS, HIT], GOLD, 2) == 0.0
    assert hit_at_k([], GOLD, 5) == 0.0


def test_reciprocal_rank() -> None:
    assert reciprocal_rank_at_k([MISS, MISS, HIT], GOLD, 10) == pytest.approx(1 / 3)
    assert reciprocal_rank_at_k([MISS, MISS, HIT], GOLD, 2) == 0.0
    assert reciprocal_rank_at_k([], GOLD, 10) == 0.0


def test_evaluate_skips_unanswerable_and_counts_a_missing_id_as_a_miss() -> None:
    out = evaluate({"q1": [HIT]}, [_answerable("q1"), _answerable("q2"), UNANSWERABLE_Q3])
    assert out == {"hit@5": 0.5, "mrr@10": 0.5, "n": 2.0}


def test_evaluate_needs_answerable_items() -> None:
    with pytest.raises(ValueError, match="no answerable items"):
        evaluate({}, [UNANSWERABLE_Q3])


def test_main_prints_scores(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    golden = tmp_path / "golden.jsonl"
    golden.write_text(
        json.dumps(_answerable("q1").model_dump(mode="json"))
        + "\n"
        + json.dumps(_answerable("q2").model_dump(mode="json"))
        + "\n"
    )
    results = tmp_path / "results.jsonl"
    results.write_text(
        json.dumps({"id": "q1", "ranked": [{"book": "B1", "page_start": 30, "page_end": 30}]})
        + "\n"
    )
    assert main(["--golden", str(golden), "--results", str(results)]) == 0
    assert json.loads(capsys.readouterr().out) == {"hit@5": 0.5, "mrr@10": 0.5, "n": 2.0}
