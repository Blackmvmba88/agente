from __future__ import annotations

import json
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


def test_cli_phase2_integrity_commands(tmp_path: Path, capsys) -> None:
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()
    first = songs_dir / "First.txt"
    second = songs_dir / "Second.txt"
    first.write_text(
        "Title: First\nArtist: Iyari Gomez\n\nSame lyrics\n",
        encoding="utf-8",
    )
    second.write_text(
        "Title: Second\nArtist: Iyari Gomez\n\nSame lyrics\n",
        encoding="utf-8",
    )
    registry_path = tmp_path / "registry.json"

    assert main(["--registry", str(registry_path), "scan", str(first)]) == 0
    capsys.readouterr()
    assert main(["--registry", str(registry_path), "scan", str(second)]) == 1
    capsys.readouterr()

    assert main(["--registry", str(registry_path), "doctor"]) == 0
    out = capsys.readouterr().out
    assert "healthy: 1 songs" in out

    assert main(["--registry", str(registry_path), "duplicates"]) == 0
    out = capsys.readouterr().out
    assert "no duplicate lyrics groups" in out

    assert main(["--registry", str(registry_path), "conflicts"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == "[]"

    assert main(["--registry", str(registry_path), "stats"]) == 0
    out = capsys.readouterr().out
    assert "songs: 1" in out
    assert "duplicate_groups: 0" in out
    assert "missing_source_fingerprints: 0" in out
    assert "missing_lyrics_fingerprints: 0" in out


def test_scan_writes_import_report_and_backup(tmp_path: Path, capsys) -> None:
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()
    source = songs_dir / "Fire.txt"
    source.write_text("Title: Fire\nArtist: Iyari Gomez\n\nBurning line\n", encoding="utf-8")
    registry_path = tmp_path / "registry.json"
    report_path = tmp_path / "reports" / "import.json"

    assert main([
        "--registry", str(registry_path), "scan", str(songs_dir),
        "--report", str(report_path),
    ]) == 0
    capsys.readouterr()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["discovered"] == 1
    assert report["indexed"] == 1
    assert report["failed"] == 0
    assert report["successes"][0]["song_id"] == "bm_song_000001"

    assert main([
        "--registry", str(registry_path), "scan", str(songs_dir),
        "--report", str(report_path),
    ]) == 0
    capsys.readouterr()

    backups = list((tmp_path / "backups").glob("registry.*.json.bak"))
    assert backups


def test_scan_report_captures_failures(tmp_path: Path, capsys) -> None:
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()
    source = songs_dir / "Unknown.txt"
    source.write_text("Lyrics only\n", encoding="utf-8")
    registry_path = tmp_path / "registry.json"
    report_path = tmp_path / "import.json"

    assert main([
        "--registry", str(registry_path), "scan", str(songs_dir),
        "--report", str(report_path),
    ]) == 1
    capsys.readouterr()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["indexed"] == 0
    assert report["failed"] == 1
    assert report["failures"][0]["error_type"] == "ValueError"
    assert "missing artist" in report["failures"][0]["error"]


def test_registry_round_trip_load(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    empty = SongRegistry()
    empty.save(registry_path)

    loaded = SongRegistry.load(registry_path)
    assert loaded.to_dict() == empty.to_dict()
