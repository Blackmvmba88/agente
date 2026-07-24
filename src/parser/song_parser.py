from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ParsedSongText:
    title: str | None
    artist: str | None
    lyrics: str


def parse_song_text(text: str, *, source_path: str | Path | None = None) -> ParsedSongText:
    """Parse a text source conservatively without inventing missing metadata.

    Supported explicit headers at the top of the document:

    Title: ...
    Artist: ...

    A leading Markdown H1 (``# Title``) is also accepted as the title.
    When no explicit title is present and a source path is supplied, the file
    stem is used as a source-derived title candidate. Artist is never inferred.
    The remaining text is preserved as lyrics apart from stripped metadata
    header lines and surrounding blank lines.
    """

    lines = text.splitlines()
    title: str | None = None
    artist: str | None = None
    consumed: set[int] = set()

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            if title is None and artist is None:
                continue
            break

        lowered = line.lower()
        if lowered.startswith("title:"):
            value = line.split(":", 1)[1].strip()
            title = value or None
            consumed.add(index)
            continue
        if lowered.startswith("artist:"):
            value = line.split(":", 1)[1].strip()
            artist = value or None
            consumed.add(index)
            continue
        if title is None and line.startswith("# "):
            value = line[2:].strip()
            title = value or None
            consumed.add(index)
            continue
        break

    if title is None and source_path is not None:
        stem = Path(source_path).stem.strip()
        title = stem or None

    lyrics_lines = [line for index, line in enumerate(lines) if index not in consumed]
    lyrics = "\n".join(lyrics_lines).strip()

    return ParsedSongText(title=title, artist=artist, lyrics=lyrics)
