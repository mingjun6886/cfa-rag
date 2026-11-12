import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


STEPS = [
    "Source PDFs", "Parse", "Chunk", "Embed", "Index",
    "Chat UI", "Service API", "Input check", "Rewrite", "Hybrid search", "Rerank",
    "Grounding gate", "Answer", "Citation check", "Respond",
    "Golden set", "Run the question flow", "Score", "Report", "CI gate",
]  # fmt: skip


def test_flow_page_has_every_step_and_no_external_requests() -> None:
    html = (ROOT / "docs" / "flow.html").read_text()
    assert [s for s in STEPS if f">{s}<" not in html] == []
    external = r'<(?:script|img|iframe|source)\b[^>]*\bsrc="https?://|<link\b[^>]*\bhref="https?://'
    assert re.findall(external, html) == []


def test_readme_diagram_uses_the_same_step_names() -> None:
    readme = (ROOT / "README.md").read_text()
    assert [s for s in STEPS if s not in readme] == []


def test_readme_relative_links_resolve() -> None:
    links = re.findall(r"\]\((?!https?://|#)([^)#]+)", (ROOT / "README.md").read_text())
    assert links
    assert [link for link in links if not (ROOT / link).exists()] == []
