import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "bakeoff_sheet", ROOT / "scripts/bakeoff_sheet.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sheet_has_one_section_per_page_with_every_parsers_output(tmp_path: Path) -> None:
    pages = tmp_path / "pages.yaml"
    pages.write_text(
        "pages:\n"
        '  - {pdf: "text_and_images.pdf", page: 1, category: formula}\n'
        '  - {pdf: "text_and_images.pdf", page: 2, category: plain}\n'
    )
    parsed = tmp_path / "parsed"
    for parser, text in (("textlayer", "x $$a<b$$"), ("docling", "<b>bold</b>")):
        folder = parsed / parser / "text_and_images"
        folder.mkdir(parents=True)
        (folder / "p0001.md").write_text(text)
    out = tmp_path / "review.html"

    _load_script().main(pages, parsed, FIXTURES, out)

    html = out.read_text()
    assert html.count('<section class="page"') == 2
    assert "text_and_images p1 (formula)" in html and "text_and_images p2 (plain)" in html
    assert "x $$a&lt;b$$" in html and "&lt;b&gt;bold&lt;/b&gt;" in html  # escaped, not injected
    assert "<b>bold</b>" not in html
    assert html.count("data:image/png;base64,") == 2  # one rendered page image per section
    assert html.count("(no output)") == 2  # neither parser has page 2
