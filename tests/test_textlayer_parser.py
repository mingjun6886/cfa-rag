from pathlib import Path

import pytest
import yaml

from cfa_rag.factory import build_formula_reader
from cfa_rag.ingestion.parsers.textlayer_parser import TextLayerParser

ROOT = Path(__file__).parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "text_and_images.pdf"


def _page_text(parser: TextLayerParser) -> str:
    return next(iter(parser.lazy_load())).page_content


def test_formulas_are_placed_in_reading_order_and_decoration_is_dropped() -> None:
    seen: list[bytes] = []

    def reader(png: bytes) -> str:
        seen.append(png)
        return "x=1"

    docs = list(TextLayerParser(FIXTURE, formula_reader=reader).lazy_load())
    assert [d.metadata["page"] for d in docs] == [1, 2, 3]
    assert docs[0].metadata == {"source": "text_and_images.pdf", "page": 1, "parser": "textlayer"}
    text = docs[0].page_content
    assert text.index("Before formula") < text.index("$$x=1$$") < text.index("After formula")
    assert "rate $x=1$ per period" in text
    assert len(seen) == 2  # the icon was never sent to the reader
    assert all(png.startswith(b"\x89PNG") for png in seen)
    assert "$" not in docs[1].page_content  # a plain page gets no empty formula blocks


def test_decoration_is_counted_across_the_whole_pdf_not_just_requested_pages() -> None:
    def reader(png: bytes) -> str:
        raise AssertionError("the icon must be recognised as decoration")

    text = _page_text(TextLayerParser(FIXTURE, pages=[2], formula_reader=reader))
    assert "Plain page 2" in text and "formula" not in text


def test_unreadable_formula_is_marked_not_dropped() -> None:
    def reader(png: bytes) -> str:
        raise RuntimeError("model down")

    text = _page_text(TextLayerParser(FIXTURE, pages=[1], formula_reader=reader))
    assert text.count("[formula unreadable]") == 2


def test_empty_reader_output_is_marked_unreadable() -> None:
    text = _page_text(TextLayerParser(FIXTURE, pages=[1], formula_reader=lambda png: "  \n"))
    assert text.count("[formula unreadable]") == 2


def test_not_a_formula_becomes_figure() -> None:
    parser = TextLayerParser(FIXTURE, pages=[1], formula_reader=lambda png: " NOT_A_FORMULA ")
    text = _page_text(parser)
    assert "[figure]" in text and "$" not in text


def test_reader_output_is_cleaned() -> None:
    parser = TextLayerParser(
        FIXTURE, pages=[1], formula_reader=lambda png: "```latex\n$$x=1$$\n```"
    )
    text = _page_text(parser)
    assert "$$x=1$$" in text and "```" not in text


NOTES_B1 = ROOT / "data" / "raw" / "NotesLV1 2024" / "CFA 2024 SCH L1 B1.pdf"


@pytest.mark.skipif(not NOTES_B1.exists(), reason="the study notes are not in this checkout")
def test_fi_ligatures_survive_on_the_real_notes() -> None:
    # pdfminer drops the "fi" glyph in these PDFs and returns "simpli ies".
    parser = TextLayerParser(NOTES_B1, pages=[30], formula_reader=lambda png: "x")
    text = _page_text(parser)
    assert "simplifies" in text and "fixed-coupon" in text and "financial" in text


def test_page_out_of_range() -> None:
    with pytest.raises(ValueError, match=r"page 9 out of range: text_and_images\.pdf has 3 pages"):
        list(TextLayerParser(FIXTURE, pages=[9]).lazy_load())


def test_reader_is_not_needed_for_pages_without_formula_images(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CFA_RAG_FORMULA_MODEL", raising=False)
    assert "Plain page 3" in _page_text(TextLayerParser(FIXTURE, pages=[3]))


def test_build_formula_reader_requires_the_model_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CFA_RAG_FORMULA_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="CFA_RAG_FORMULA_MODEL is not set"):
        build_formula_reader()


def test_formula_reader_prompt_is_pinned() -> None:
    prompt = yaml.safe_load((ROOT / "configs/prompts/formula_reader.v1.yaml").read_text())["prompt"]
    assert prompt == (
        "Transcribe the formula in this image to LaTeX. Output only the LaTeX, with no "
        "delimiters and no commentary. If the image is not a mathematical formula, output "
        "exactly NOT_A_FORMULA."
    )
