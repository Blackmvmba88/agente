from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Song:
    """Canonical immutable song record for BlackMamba Agent v0.1."""

    song_id: str
    title: str
    artist: str
    lyrics_id: str
    lyrics: str
    source_type: str
    source_path: str
    status: str = "indexed"

    def to_dict(self) -> dict[str, object]:
        return {
            "song_id": self.song_id,
            "title": self.title,
            "artist": self.artist,
            "lyrics_id": self.lyrics_id,
            "lyrics": self.lyrics,
            "source": {
                "type": self.source_type,
                "path": self.source_path,
            },
            "status": self.status,
        }
