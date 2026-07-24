from __future__ import annotations

from pathlib import Path


SUPPORTED_SUFFIXES = {".txt", ".md"}


def read_text_source(path: str | Path) -> str:
    source = Path(path)

    if not source.is_file():
        raise FileNotFoundError(source)

    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"unsupported text source: {source.suffix or '<none>'}")

    return source.read_text(encoding="utf-8")
