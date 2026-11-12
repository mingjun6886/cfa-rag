import importlib.util
from pathlib import Path
from types import ModuleType

import pypdfium2 as pdfium

ROOT = Path(__file__).parent.parent
COMMITTED = ROOT / "sample" / "corpus" / "time-value-of-money.pdf"


def _builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_sample", ROOT / "sample/build_sample.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pages_text(path: Path) -> list[str]:
    pdf = pdfium.PdfDocument(path)
    try:
        return [page.get_textpage().get_text_range() for page in pdf]
    finally:
        pdf.close()


def test_built_pdf_has_the_sections_and_the_table(tmp_path: Path) -> None:
    out = tmp_path / "sample.pdf"
    _builder().build(out)
    text = "\n".join(_pages_text(out))
    for heading in ("Future value of a single sum", "Present value of a single sum", "Annuities",
                    "Perpetuities", "Net present value"):  # fmt: skip
        assert heading in text
    assert "2.5937" in text  # last cell of the future-value table


def test_committed_pdf_matches_the_source(tmp_path: Path) -> None:
    fresh = tmp_path / "fresh.pdf"
    _builder().build(fresh)
    assert _pages_text(COMMITTED) == _pages_text(fresh), "run: uv run python sample/build_sample.py"
