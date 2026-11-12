from pathlib import Path

import pytest
from langchain_core.documents import Document

from cfa_rag.factory import build_parser
from cfa_rag.ingestion.parse import parse_page_spec, write_pages

FIXTURE = Path(__file__).parent / "fixtures" / "text_and_images.pdf"


def test_parse_page_spec() -> None:
    assert parse_page_spec("30,31,45-47") == [30, 31, 45, 46, 47]


def test_write_pages_keeps_parsers_apart(tmp_path: Path) -> None:
    a = Document(page_content="A", metadata={"source": "b1.pdf", "page": 30, "parser": "textlayer"})
    b = Document(page_content="B", metadata={"source": "b1.pdf", "page": 30, "parser": "docling"})
    paths = write_pages([a, b], tmp_path)
    assert paths == [tmp_path / "textlayer/b1/p0030.md", tmp_path / "docling/b1/p0030.md"]
    assert [p.read_text() for p in paths] == ["A", "B"]


def test_unknown_parser_lists_known_names() -> None:
    with pytest.raises(ValueError, match="docling, mistral, textlayer"):
        build_parser("nope", FIXTURE)
