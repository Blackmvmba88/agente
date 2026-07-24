from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AssetRef:
    """Reference from a canonical song to one related catalog asset."""

    asset_id: str
    asset_type: str
    status: str = "linked"

    def to_dict(self) -> dict[str, str]:
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class CatalogAsset:
    """Canonical metadata shell for non-song assets introduced in Phase 3."""

    asset_id: str
    asset_type: str
    source_type: str | None = None
    source_path: str | None = None
    status: str = "indexed"

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "status": self.status,
        }
        if self.source_type is not None or self.source_path is not None:
            payload["source"] = {
                "type": self.source_type,
                "path": self.source_path,
            }
        return payload
