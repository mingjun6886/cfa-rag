"""Builds sample/corpus/time-value-of-money.pdf from sample/time-value-of-money.md.

The source uses a small subset of Markdown: `# ` title, `## ` heading, four-space indented
lines as formulas, `|`-separated rows as a table, blank lines between paragraphs.

Run: uv run python sample/build_sample.py
"""

from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF

HERE = Path(__file__).parent
SOURCE = HERE / "time-value-of-money.md"
OUT = HERE / "corpus" / "time-value-of-money.pdf"


def _table(pdf: FPDF, rows: list[list[str]]) -> None:
    with pdf.table(text_align="CENTER", width=120, align="LEFT") as table:
        for cells in rows:
            row = table.row()
            for cell in cells:
                row.cell(cell)
    pdf.ln(3)


def build(out: Path = OUT, source: Path = SOURCE) -> None:
    pdf = FPDF(format="A4")
    pdf.set_creation_date(datetime(2026, 11, 12, tzinfo=UTC))  # same bytes on every build
    pdf.set_title("Time Value of Money: A Short Primer")
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    paragraph: list[str] = []
    table: list[list[str]] = []

    def flush() -> None:
        if paragraph:
            pdf.set_font("helvetica", size=11)
            pdf.multi_cell(0, 6, " ".join(paragraph), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            paragraph.clear()
        if table:
            _table(pdf, table)
            table.clear()

    for line in source.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") or line.startswith("# "):
            flush()
            title = line.startswith("# ")
            pdf.set_font("helvetica", style="B", size=18 if title else 14)
            pdf.ln(2)
            pdf.multi_cell(0, 9, line.lstrip("# "), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif line.startswith("    "):
            flush()
            pdf.set_font("courier", size=11)
            pdf.cell(0, 7, "    " + line.strip(), new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("|"):
            if paragraph:
                flush()
            table.append([cell.strip() for cell in line.strip("|").split("|")])
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
    flush()
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))


if __name__ == "__main__":
    build()
    print(f"wrote {OUT}")
