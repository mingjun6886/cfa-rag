"""Detects text copied from the study notes, so the public golden set stays in the owner's words."""

import re
from collections.abc import Sequence

from cfa_rag.evaluation.golden import GoldenItem


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _haystack(corpus: str) -> str:
    """The corpus as lower-case words with single spaces, padded so whole words can be matched."""
    return f" {' '.join(_words(corpus))} "


def _shared(text: str, haystack: str, n: int) -> set[str]:
    words = _words(text)
    grams = {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}
    return {gram for gram in grams if f" {gram} " in haystack}


def shared_ngrams(text: str, corpus: str, n: int = 8) -> set[str]:
    """Word n-grams of `text` that also occur in `corpus`, ignoring case, punctuation, spacing."""
    return _shared(text, _haystack(corpus), n)


def find_copied(items: Sequence[GoldenItem], corpus: str, n: int = 8) -> dict[str, set[str]]:
    """Map the id of each item whose question or reference answer copies `corpus` to the n-grams."""
    haystack = _haystack(corpus)  # normalised once, not once per item
    found: dict[str, set[str]] = {}
    for item in items:
        hits = _shared(f"{item.question} {item.reference_answer or ''}", haystack, n)
        if hits:
            found[item.id] = hits
    return found
