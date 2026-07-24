from __future__ import annotations

from pathlib import Path

from src.cli import main
from src.registry.registry import SongRegistry


def test_cli_scan_list_show_search_validate(tmp_path: Path, capsys) -> None:
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()
    source = songs_dir / "Fire.txt"
    source.write_text("Title: Fire\nArtist: Iyari Gomez\n\nBurning line\n", encoding="utf-8")
    registry_path = tmp_path / "registry.json"

    assert main(["--registry", str(registry_path), "scan", str(songs_dir)]) == 0
    out = capsys.readouterr().out
    assert "indexed bm_song_000001" in out

    assert main(["--registry", str(registry_path), "list"]) == 0
    out = capsys.readouterr().out
    assert "bm_song_000001\tFire\tIyari Gomez" in out

    assert main(["--registry", str(registry_path), "show", "bm_song_000001"]) == 0
    out = capsys.readouterr().out
    assert "lyrics_id: bm_lyrics_000001" in out
    assert "Burning line" in out

    assert main(["--registry", str(registry_path), "search", "burning"]) == 0
    out = capsys.readouterr().out
    assert "bm_song_000001\tFire\tIyari Gomez" in out

    assert main(["--registry", str(registry_path), "validate"]) == 0
    out = capsys.readouterr().out
    assert "ok: 1 songs" in out


def test_registry_round_trip_load(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    empty = SongRegistry()
    empty.save(registry_path)

    loaded = SongRegistry.load(registry_path)
    assert loaded.to_dict() == empty.to_dict()
