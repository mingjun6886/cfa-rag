"""Formula reader backed by a vision model served by Ollama."""

import base64
from collections.abc import Callable
from pathlib import Path

import yaml
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

# shortcut: finds the prompt relative to the source checkout, so it works for an editable
# install only; add a configurable config directory when the package is distributed.
_PROMPT_FILE = Path(__file__).parents[4] / "configs" / "prompts" / "formula_reader.v1.yaml"


def make_formula_reader(model: str) -> Callable[[bytes], str]:
    """Return a function that sends PNG bytes to `model` and returns its raw reply."""
    prompt: str = yaml.safe_load(_PROMPT_FILE.read_text(encoding="utf-8"))["prompt"]
    llm = ChatOllama(model=model, temperature=0, num_predict=512)

    def read(png: bytes) -> str:
        data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": data_url},
            ]
        )
        reply = llm.invoke([message]).content
        return reply if isinstance(reply, str) else ""

    return read
