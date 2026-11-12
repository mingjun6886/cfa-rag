"""Page selection shared by every parser adapter."""

from collections.abc import Sequence


def check_pages(pages: Sequence[int] | None, page_count: int, pdf_name: str) -> list[int]:
    """Return the 1-indexed pages to parse in ascending order; all pages when `pages` is None."""
    if pages is None:
        return list(range(1, page_count + 1))
    for page in pages:
        if not 1 <= page <= page_count:
            raise ValueError(f"page {page} out of range: {pdf_name} has {page_count} pages")
    return sorted(set(pages))


def contiguous_runs(pages: Sequence[int]) -> list[tuple[int, int]]:
    """Group ascending pages into inclusive (first, last) runs: [1, 2, 3, 7] -> [(1, 3), (7, 7)]."""
    runs: list[tuple[int, int]] = []
    for page in pages:
        if runs and page == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], page)
        else:
            runs.append((page, page))
    return runs
