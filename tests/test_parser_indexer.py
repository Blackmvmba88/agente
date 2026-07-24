from __future__ import annotations

from pathlib import Path

import pytest

from src.indexer import index_text_source
from src.parser.song_parser import parse_song_text
from src.registry.registry import SongRegistry


def test_parser_reads_explicit_headers() -> None:
    parsed = parse_song_text("Title: Fire\nArtist: Iyari Gomez\n\nLine one\nLine two\n")

    assert parsed.title == "Fire"
    assert parsed.artist == "Iyari Gomez"
    assert parsed.lyrics == "Line one\nLine two"


def test_parser_accepts_markdown_h1() -> None:
    parsed = parse_song_text("# Desert Moon\n\nFirst line\n", source_path="ignored.txt")

    assert parsed.title == "Desert Moon"
    assert parsed.artist is None
    assert parsed.lyrics == "First line"


def test_parser_uses_filename_stem_but_never_invents_artist() -> None:
    parsed = parse_song_text("First line\nSecond line\n", source_path="songs/Welcome to Dubai.txt")

    assert parsed.title == "Welcome to Dubai"
    assert parsed.artist is None
    assert parsed.lyrics == "First line\nSecond line"


def test_indexer_assigns_monotonic_canonical_ids(tmp_path: Path) -> None:
    first = tmp_path / "First Song.txt"
    second = tmp_path / "Second Song.txt"
    first.write_text("Alpha\n", encoding="utf-8")
    second.write_text("Beta\n", encoding="utf-8")

    registry = SongRegistry()

    song1 = index_text_source(first, registry, default_artist="Iyari Gomez")
    song2 = index_text_source(second, registry, default_artist="Iyari Gomez")

    assert song1.song_id == "bm_song_000001"
    assert song1.lyrics_id == "bm_lyrics_000001"
    assert song2.song_id == "bm_song_000002"
    assert song2.lyrics_id == "bm_lyrics_000002"


def test_indexer_preserves_source_bytes(tmp_path: Path) -> None:
    source = tmp_path / "Preserved.txt"
    original = b"Title: Preserved\nArtist: Iyari Gomez\n\nNever touch this.\n"
    source.write_bytes(original)

    registry = SongRegistry()
    index_text_source(source, registry)

    assert source.read_bytes() == original


def test_indexer_rejects_missing_artist_without_default(tmp_path: Path) -> None:
    source = tmp_path / "Unknown Artist.txt"
    source.write_text("Lyrics only\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing artist"):
        index_text_source(source, SongRegistry())
