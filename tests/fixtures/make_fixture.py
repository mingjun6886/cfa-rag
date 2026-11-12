"""Builds tests/fixtures/text_and_images.pdf: three pages of text, one recurring icon, two formulas.

Page 1, top to bottom: "Before formula", a display formula image, "After formula", then the
line "rate <inline formula image> per period". Pages 2 and 3 hold one line of text each. The same
small icon sits on all three pages, so a parser must treat it as decoration.

Run: uv run python tests/fixtures/make_fixture.py
"""

import tempfile
from pathlib import Path

from fpdf import FPDF
from PIL import Image

OUT = Path(__file__).parent / "text_and_images.pdf"


def _png(directory: Path, name: str, size: tuple[int, int], colour: tuple[int, int, int]) -> str:
    path = directory / name
    Image.new("RGB", size, colour).save(path)
    return str(path)


def build(out: Path = OUT) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        icon = _png(Path(tmp), "icon.png", (16, 16), (200, 30, 30))
        display = _png(Path(tmp), "display.png", (160, 60), (30, 30, 200))
        inline = _png(Path(tmp), "inline.png", (80, 48), (30, 160, 30))

        pdf = FPDF(unit="pt", format=(595, 842))
        pdf.set_font("helvetica", size=12)

        pdf.add_page()
        pdf.image(icon, x=500, y=40, w=16, h=16)
        pdf.set_xy(72, 100)
        pdf.cell(200, 14, "Before formula")
        pdf.image(display, x=100, y=130, w=80, h=30)
        pdf.set_xy(72, 180)
        pdf.cell(200, 14, "After formula")
        pdf.set_xy(72, 220)
        pdf.cell(30, 14, "rate")
        pdf.image(inline, x=110, y=212, w=40, h=24)
        pdf.set_xy(160, 220)
        pdf.cell(100, 14, "per period")

        for n in (2, 3):
            pdf.add_page()
            pdf.image(icon, x=500, y=40, w=16, h=16)
            pdf.set_xy(72, 100)
            pdf.cell(200, 14, f"Plain page {n}")

        pdf.output(str(out))


if __name__ == "__main__":
    build()
    print(f"wrote {OUT}")
