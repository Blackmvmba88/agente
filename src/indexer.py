from __future__ import annotations

import hashlib
from pathlib import Path

from .parser.song_parser import parse_song_text
from .reader.text_reader import read_text_source
from .registry.registry import SongRegistry
from .registry.song import Song


def _next_numeric_id(prefix: str, existing: set[str]) -> str:
    highest = 0
    for value in existing:
        if not value.startswith(prefix):
            continue
        suffix = value.removeprefix(prefix)
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1:06d}"


def source_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def index_text_source(
    path: str | Path,
    registry: SongRegistry,
    *,
    default_artist: str | None = None,
) -> Song:
    """Read and index one supported text source without modifying it."""

    source = Path(path)
    text = read_text_source(source)
    parsed = parse_song_text(text, source_path=source)

    if not parsed.title:
        raise ValueError(f"missing title: {source}")

    artist = parsed.artist or default_artist
    if not artist:
        raise ValueError(f"missing artist: {source}")

    song_id = _next_numeric_id("bm_song_", {song.song_id for song in registry.songs})
    lyrics_id = _next_numeric_id("bm_lyrics_", {song.lyrics_id for song in registry.songs})

    song = Song(
        song_id=song_id,
        title=parsed.title,
        artist=artist,
        lyrics_id=lyrics_id,
        lyrics=parsed.lyrics,
        source_type="text",
        source_path=str(source),
    )
    registry.add(song)
    return song
