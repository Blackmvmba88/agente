from __future__ import annotations

import json
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

    def to_dict(self) -> dict[str, object]:
        ordered = sorted(self.songs, key=lambda song: song.song_id)
        return {
            "schema_version": SCHEMA_VERSION,
            "songs": [song.to_dict() for song in ordered],
        }

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
