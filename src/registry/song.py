from __future__ import annotations

from dataclasses import dataclass

from .assets import AssetRef


@dataclass(frozen=True, slots=True)
class Song:
    """Canonical immutable song record for BlackMamba Agent."""

    song_id: str
    title: str
    artist: str
    lyrics_id: str
    lyrics: str
    source_type: str
    source_path: str
    source_fingerprint: str | None = None
    lyrics_fingerprint: str | None = None
    relationships: tuple[AssetRef, ...] = ()
    status: str = "indexed"

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
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
        if self.source_fingerprint is not None:
            payload["source_fingerprint"] = self.source_fingerprint
        if self.lyrics_fingerprint is not None:
            payload["lyrics_fingerprint"] = self.lyrics_fingerprint
        if self.relationships:
            payload["relationships"] = [relationship.to_dict() for relationship in self.relationships]
        return payload
