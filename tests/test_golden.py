import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from cfa_rag.evaluation.golden import GoldenItem, PageRef, load_golden

OK_ITEM: dict[str, Any] = {
    "id": "q1",
    "question": "What is a perpetuity?",
    "language": "en",
    "kind": "answerable",
    "reference_answer": "A stream of equal payments that never ends.",
    "sources": [{"book": "B1", "pages": [30]}],
}
UNANSWERABLE: dict[str, Any] = {
    "id": "u1",
    "question": "Who won the football World Cup in 1998?",
    "language": "en",
    "kind": "unanswerable",
}


def _write(path: Path, *lines: object) -> Path:
    path.write_text("\n".join(x if isinstance(x, str) else json.dumps(x) for x in lines) + "\n")
    return path


def test_loads_valid_items(tmp_path: Path) -> None:
    items = load_golden(_write(tmp_path / "g.jsonl", OK_ITEM, "", UNANSWERABLE))
    assert [i.id for i in items] == ["q1", "u1"]
    assert items[0].sources == [PageRef(book="B1", pages=[30])]
    assert items[1].reference_answer is None and items[1].sources == []


def test_bad_line_is_reported_with_its_number(tmp_path: Path) -> None:
    f = _write(tmp_path / "g.jsonl", OK_ITEM, {"id": "q2", "question": "?"})
    with pytest.raises(ValueError, match=r"^line 2:"):
        load_golden(f)


def test_malformed_json_is_reported_with_its_number(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"^line 1:"):
        load_golden(_write(tmp_path / "g.jsonl", "{not json"))


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"^line 2: duplicate id 'q1'"):
        load_golden(_write(tmp_path / "g.jsonl", OK_ITEM, OK_ITEM))


def test_answerable_needs_an_answer_and_a_source() -> None:
    with pytest.raises(ValidationError):
        GoldenItem(**{**OK_ITEM, "sources": []})
    with pytest.raises(ValidationError):
        GoldenItem(**{**OK_ITEM, "reference_answer": None})


def test_unanswerable_has_neither_answer_nor_source() -> None:
    with pytest.raises(ValidationError):
        GoldenItem(**{**UNANSWERABLE, "reference_answer": "something"})
    with pytest.raises(ValidationError):
        GoldenItem(**{**UNANSWERABLE, "sources": OK_ITEM["sources"]})


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        GoldenItem(**{**OK_ITEM, "quesiton": "typo"})


@pytest.mark.parametrize("ref", [{"book": "B9", "pages": [1]}, {"book": "B1", "pages": []},
                                 {"book": "B1", "pages": [0]}])  # fmt: skip
def test_page_refs_are_validated(ref: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        PageRef(**ref)
