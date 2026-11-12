import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_readme_relative_links_resolve() -> None:
    links = re.findall(r"\]\((?!https?://|#)([^)#]+)", (ROOT / "README.md").read_text())
    assert links
    assert [link for link in links if not (ROOT / link).exists()] == []
