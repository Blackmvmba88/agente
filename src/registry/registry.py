from __future__ import annotations

import json
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .assets import AssetRef, CatalogAsset
from .song import Song


SCHEMA_VERSION = 2
ASSET_PREFIXES = {
    "lyrics": "bm_lyrics_",
    "audio": "bm_audio_",
    "artwork": "bm_artwork_",
    "release": "bm_release_",
}


def migrate_payload(payload: dict[str, object]) -> dict[str, object]:
    """Migrate an older registry payload to the current schema without changing IDs."""

    version = payload.get("schema_version", 1)
    if not isinstance(version, int):
        raise ValueError(f"invalid schema_version: {version!r}")
    if version > SCHEMA_VERSION:
        raise ValueError(f"unsupported future schema_version: {version}")

    migrated = dict(payload)
    if version == 1:
        migrated.setdefault("assets", [])
        migrated["schema_version"] = 2
    return migrated


@dataclass
class SongRegistry:
    songs: list[Song] = field(default_factory=list)
    assets: list[CatalogAsset] = field(default_factory=list)

    def add(self, song: Song) -> None:
        if any(existing.song_id == song.song_id for existing in self.songs):
            raise ValueError(f"duplicate song_id: {song.song_id}")
        if any(existing.lyrics_id == song.lyrics_id for existing in self.songs):
            raise ValueError(f"duplicate lyrics_id: {song.lyrics_id}")
        self.songs.append(song)

    def add_asset(self, asset: CatalogAsset) -> None:
        if any(existing.asset_id == asset.asset_id for existing in self.assets):
            raise ValueError(f"duplicate asset_id: {asset.asset_id}")
        expected_prefix = ASSET_PREFIXES.get(asset.asset_type)
        if expected_prefix and not asset.asset_id.startswith(expected_prefix):
            raise ValueError(f"invalid {asset.asset_type} asset_id: {asset.asset_id}")
        self.assets.append(asset)

    def get(self, song_id: str) -> Song | None:
        return next((song for song in self.songs if song.song_id == song_id), None)

    def get_asset(self, asset_id: str) -> CatalogAsset | None:
        return next((asset for asset in self.assets if asset.asset_id == asset_id), None)

    def relationships_for(self, song_id: str) -> tuple[AssetRef, ...]:
        song = self.get(song_id)
        return song.relationships if song else ()

    def find_by_source_fingerprint(self, fingerprint: str) -> Song | None:
        return next(
            (song for song in self.songs if song.source_fingerprint == fingerprint),
            None,
        )

    def find_by_lyrics_fingerprint(self, fingerprint: str) -> list[Song]:
        return [song for song in self.songs if song.lyrics_fingerprint == fingerprint]

    def duplicate_groups(self) -> list[list[Song]]:
        groups: dict[str, list[Song]] = defaultdict(list)
        for song in self.songs:
            if song.lyrics_fingerprint:
                groups[song.lyrics_fingerprint].append(song)
        return [
            sorted(group, key=lambda item: item.song_id)
            for group in groups.values()
            if len(group) > 1
        ]

    def conflict_report(self) -> list[dict[str, object]]:
        conflicts: list[dict[str, object]] = []
        for group in self.duplicate_groups():
            conflicts.append(
                {
                    "type": "duplicate_lyrics",
                    "lyrics_fingerprint": group[0].lyrics_fingerprint,
                    "song_ids": [song.song_id for song in group],
                    "sources": [song.source_path for song in group],
                }
            )
        return conflicts

    def doctor(self) -> list[str]:
        errors = self.validate()
        warnings: list[str] = []

        for song in self.songs:
            if not song.source_fingerprint:
                warnings.append(f"missing source_fingerprint: {song.song_id}")
            if not song.lyrics_fingerprint:
                warnings.append(f"missing lyrics_fingerprint: {song.song_id}")

        for conflict in self.conflict_report():
            warnings.append(
                "duplicate lyrics fingerprint: "
                + ", ".join(conflict["song_ids"])
            )

        return errors + warnings

    def stats(self) -> dict[str, int]:
        duplicate_groups = self.duplicate_groups()
        duplicate_records = sum(len(group) for group in duplicate_groups)
        return {
            "songs": len(self.songs),
            "assets": len(self.assets),
            "relationships": sum(len(song.relationships) for song in self.songs),
            "duplicate_groups": len(duplicate_groups),
            "duplicate_records": duplicate_records,
            "missing_source_fingerprints": sum(
                1 for song in self.songs if not song.source_fingerprint
            ),
            "missing_lyrics_fingerprints": sum(
                1 for song in self.songs if not song.lyrics_fingerprint
            ),
        }

    def search(self, query: str) -> list[Song]:
        needle = query.casefold()
        return [
            song
            for song in self.songs
            if needle in song.song_id.casefold()
            or needle in song.title.casefold()
            or needle in song.artist.casefold()
            or needle in song.lyrics.casefold()
        ]

    def validate(self) -> list[str]:
        errors: list[str] = []
        song_ids: set[str] = set()
        lyrics_ids: set[str] = set()
        asset_ids: set[str] = set()

        for asset in self.assets:
            if asset.asset_id in asset_ids:
                errors.append(f"duplicate asset_id: {asset.asset_id}")
            asset_ids.add(asset.asset_id)

        for song in self.songs:
            if song.song_id in song_ids:
                errors.append(f"duplicate song_id: {song.song_id}")
            song_ids.add(song.song_id)

            if song.lyrics_id in lyrics_ids:
                errors.append(f"duplicate lyrics_id: {song.lyrics_id}")
            lyrics_ids.add(song.lyrics_id)

            if not song.title.strip():
                errors.append(f"missing title: {song.song_id}")
            if not song.artist.strip():
                errors.append(f"missing artist: {song.song_id}")

            for relationship in song.relationships:
                if relationship.asset_type == "lyrics" and relationship.asset_id == song.lyrics_id:
                    continue
                if relationship.asset_id not in asset_ids:
                    errors.append(
                        f"missing related asset: {song.song_id} -> {relationship.asset_id}"
                    )

        return errors

    def to_dict(self) -> dict[str, object]:
        ordered_songs = sorted(self.songs, key=lambda song: song.song_id)
        ordered_assets = sorted(self.assets, key=lambda asset: asset.asset_id)
        return {
            "schema_version": SCHEMA_VERSION,
            "songs": [song.to_dict() for song in ordered_songs],
            "assets": [asset.to_dict() for asset in ordered_assets],
        }

    @classmethod
    def load(cls, path: str | Path) -> "SongRegistry":
        source = Path(path)
        if not source.exists():
            return cls()

        payload = json.loads(source.read_text(encoding="utf-8"))
        payload = migrate_payload(payload)

        registry = cls()
        for asset_item in payload.get("assets", []):
            source_info = asset_item.get("source") or {}
            registry.add_asset(
                CatalogAsset(
                    asset_id=asset_item["asset_id"],
                    asset_type=asset_item["asset_type"],
                    source_type=source_info.get("type"),
                    source_path=source_info.get("path"),
                    status=asset_item.get("status", "indexed"),
                )
            )

        for item in payload.get("songs", []):
            source_info = item["source"]
            relationships = tuple(
                AssetRef(
                    asset_id=relationship["asset_id"],
                    asset_type=relationship["asset_type"],
                    status=relationship.get("status", "linked"),
                )
                for relationship in item.get("relationships", [])
            )
            registry.add(
                Song(
                    song_id=item["song_id"],
                    title=item["title"],
                    artist=item["artist"],
                    lyrics_id=item["lyrics_id"],
                    lyrics=item["lyrics"],
                    source_type=source_info["type"],
                    source_path=source_info["path"],
                    source_fingerprint=item.get("source_fingerprint"),
                    lyrics_fingerprint=item.get("lyrics_fingerprint"),
                    relationships=relationships,
                    status=item.get("status", "indexed"),
                )
            )
        return registry

    def backup(self, path: str | Path, *, backup_dir: str | Path | None = None) -> Path | None:
        source = Path(path)
        if not source.exists():
            return None

        destination_dir = Path(backup_dir) if backup_dir else source.parent / "backups"
        destination_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = destination_dir / f"{source.stem}.{stamp}{source.suffix}.bak"
        shutil.copy2(source, destination)
        return destination

    def save(self, path: str | Path, *, backup: bool = False) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if backup:
            self.backup(target)
        payload = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        target.write_text(payload + "\n", encoding="utf-8")
