from __future__ import annotations

import json
from pathlib import Path

from src.registry.assets import AssetRef, CatalogAsset
from src.registry.registry import SCHEMA_VERSION, SongRegistry
from src.registry.song import Song


def make_song(*, relationships: tuple[AssetRef, ...] = ()) -> Song:
    return Song(
        song_id="bm_song_000001",
        title="Welcome to Dubai",
        artist="Iyari Gomez",
        lyrics_id="bm_lyrics_000001",
        lyrics="Test lyrics",
        source_type="text",
        source_path="songs/welcome_to_dubai.txt",
        relationships=relationships,
    )


def test_registry_migrates_v1_payload_without_changing_ids(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    payload = {
        "schema_version": 1,
        "songs": [make_song().to_dict()],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    registry = SongRegistry.load(path)

    assert registry.get("bm_song_000001") is not None
    assert registry.get("bm_song_000001").lyrics_id == "bm_lyrics_000001"
    assert registry.assets == []
    assert registry.to_dict()["schema_version"] == SCHEMA_VERSION


def test_registry_serializes_related_assets() -> None:
    audio = CatalogAsset(
        asset_id="bm_audio_000001",
        asset_type="audio",
        source_type="file",
        source_path="audio/welcome_to_dubai.wav",
    )
    song = make_song(
        relationships=(AssetRef(asset_id=audio.asset_id, asset_type="audio"),)
    )
    registry = SongRegistry(songs=[song], assets=[audio])

    payload = registry.to_dict()

    assert payload["assets"][0]["asset_id"] == "bm_audio_000001"
    assert payload["songs"][0]["relationships"][0]["asset_id"] == "bm_audio_000001"
    assert registry.validate() == []


def test_registry_reports_missing_related_asset() -> None:
    song = make_song(
        relationships=(AssetRef(asset_id="bm_artwork_000001", asset_type="artwork"),)
    )
    registry = SongRegistry(songs=[song])

    assert registry.validate() == [
        "missing related asset: bm_song_000001 -> bm_artwork_000001"
    ]


def test_asset_prefixes_are_type_safe() -> None:
    registry = SongRegistry()

    try:
        registry.add_asset(CatalogAsset(asset_id="bm_audio_000001", asset_type="artwork"))
    except ValueError as exc:
        assert "invalid artwork asset_id" in str(exc)
    else:
        raise AssertionError("expected invalid asset prefix to be rejected")
