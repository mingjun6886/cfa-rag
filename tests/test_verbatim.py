from cfa_rag.evaluation.golden import GoldenItem, PageRef
from cfa_rag.evaluation.verbatim import find_copied, shared_ngrams

CORPUS = "Some bonds exist that have no maturity date. We refer to these as perpetual bonds."


def test_copied_sentence_is_caught_despite_case_punctuation_and_spacing() -> None:
    copied = shared_ngrams(
        "Note: SOME bonds exist that have   no maturity date, apparently.", CORPUS
    )
    assert copied == {"some bonds exist that have no maturity date"}


def test_paraphrase_passes() -> None:
    assert shared_ngrams("A perpetuity pays forever and never returns principal.", CORPUS) == set()


def test_short_text_cannot_match() -> None:
    assert shared_ngrams("some bonds exist", CORPUS) == set()


def _item(item_id: str, answer: str) -> GoldenItem:
    return GoldenItem(
        id=item_id,
        question="Why does a perpetuity have no future value?",
        language="en",
        kind="answerable",
        reference_answer=answer,
        sources=[PageRef(book="B1", pages=[30])],
    )


def test_find_copied_reports_only_the_offending_items() -> None:
    clean = _item("q1", "Payments continue forever, so there is no end point to compound to.")
    copied = _item("q2", "Some bonds exist that have no maturity date, per the text.")
    assert set(find_copied([clean, copied], CORPUS)) == {"q2"}
