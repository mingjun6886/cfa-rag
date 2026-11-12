"""Schema and loader for the golden question set (JSON Lines, one item per line)."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

Book = Literal["B1", "B2", "B3", "B4", "B5", "QS"]
Page = Annotated[int, Field(ge=1)]


class PageRef(BaseModel):
    """Pages of one book that support an answer (1-indexed, as printed in the PDF viewer)."""

    model_config = ConfigDict(extra="forbid")

    book: Book
    pages: Annotated[list[Page], Field(min_length=1)]


class GoldenItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(min_length=1)]
    question: Annotated[str, Field(min_length=1)]
    language: Literal["en", "vi"]
    kind: Literal["answerable", "unanswerable"]
    reference_answer: str | None = None
    sources: list[PageRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def _answer_and_sources_match_kind(self) -> Self:
        if self.kind == "answerable":
            if not self.reference_answer or not self.sources:
                raise ValueError("an answerable item needs a reference answer and a source")
        elif self.reference_answer is not None or self.sources:
            raise ValueError("an unanswerable item has no reference answer and no sources")
        return self


def load_golden(path: Path) -> list[GoldenItem]:
    """Read a golden file; any bad line raises ValueError starting `line <n>:` (1-indexed)."""
    items: list[GoldenItem] = []
    seen: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = GoldenItem.model_validate_json(line)
        except ValidationError as error:
            problems = "; ".join(
                f"{'.'.join(map(str, e['loc'])) or 'item'}: {e['msg']}" for e in error.errors()
            )
            raise ValueError(f"line {number}: {problems}") from error
        if item.id in seen:
            raise ValueError(f"line {number}: duplicate id {item.id!r}")
        seen.add(item.id)
        items.append(item)
    return items
