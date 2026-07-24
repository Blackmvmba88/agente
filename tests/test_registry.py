from pathlib import Path

import pytest

from src.reader.text_reader import read_text_source
from src.registry.registry import SongRegistry
from src.registry.song import Song


def make_song(song_id: str = "bm_song_000001", lyrics_id: str = "bm_lyrics_000001") -> Song:
    return Song(
        song_id=song_id,
        title="Welcome to Dubai",
        artist="Iyari Gomez",
        lyrics_id=lyrics_id,
        lyrics="Test lyrics",
        source_type="text",
        source_path="songs/welcome_to_dubai.txt",
    )


def test_song_is_immutable() -> None:
    song = make_song()
    with pytest.raises(Exception):
        song.title = "Changed"


def test_registry_rejects_duplicate_song_id() -> None:
    registry = SongRegistry()
    registry.add(make_song())

    with pytest.raises(ValueError, match="duplicate song_id"):
        registry.add(make_song(lyrics_id="bm_lyrics_000002"))


def test_registry_rejects_duplicate_lyrics_id() -> None:
    registry = SongRegistry()
    registry.add(make_song())

    with pytest.raises(ValueError, match="duplicate lyrics_id"):
        registry.add(make_song(song_id="bm_song_000002"))


def test_registry_serialization_is_deterministic(tmp_path: Path) -> None:
    registry = SongRegistry()
    registry.add(make_song("bm_song_000002", "bm_lyrics_000002"))
    registry.add(make_song("bm_song_000001", "bm_lyrics_000001"))

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    registry.save(first)
    registry.save(second)

    assert first.read_bytes() == second.read_bytes()


def test_reader_does_not_modify_source(tmp_path: Path) -> None:
    source = tmp_path / "song.txt"
    source.write_text("Title\n\nLyrics", encoding="utf-8")
    before = source.read_bytes()

    assert read_text_source(source) == "Title\n\nLyrics"
    assert source.read_bytes() == before


def test_reader_rejects_unsupported_files(tmp_path: Path) -> None:
    source = tmp_path / "song.mp3"
    source.write_bytes(b"not audio")

    with pytest.raises(ValueError, match="unsupported text source"):
        read_text_source(source)
