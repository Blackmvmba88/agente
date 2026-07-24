from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .song import Song


SCHEMA_VERSION = 1


@dataclass
class SongRegistry:
    songs: list[Song] = field(default_factory=list)

    def add(self, song: Song) -> None:
        if any(existing.song_id == song.song_id for existing in self.songs):
            raise ValueError(f"duplicate song_id: {song.song_id}")
        if any(existing.lyrics_id == song.lyrics_id for existing in self.songs):
            raise ValueError(f"duplicate lyrics_id: {song.lyrics_id}")
        self.songs.append(song)

    def get(self, song_id: str) -> Song | None:
        return next((song for song in self.songs if song.song_id == song_id), None)

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

        return errors

    def to_dict(self) -> dict[str, object]:
        ordered = sorted(self.songs, key=lambda song: song.song_id)
        return {
            "schema_version": SCHEMA_VERSION,
            "songs": [song.to_dict() for song in ordered],
        }

    @classmethod
    def load(cls, path: str | Path) -> "SongRegistry":
        source = Path(path)
        if not source.exists():
            return cls()

        payload = json.loads(source.read_text(encoding="utf-8"))
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {payload.get('schema_version')}")

        registry = cls()
        for item in payload.get("songs", []):
            source_info = item["source"]
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
                    status=item.get("status", "indexed"),
                )
            )
        return registry

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        target.write_text(payload + "\n", encoding="utf-8")
