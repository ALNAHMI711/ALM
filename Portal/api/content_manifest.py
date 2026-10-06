"""Versioned content-pack manifest registry.

The manifest is metadata only: access control stays in the authenticated
account entitlement and device-product binding layers.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import re

_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

@dataclass(frozen=True)
class ContentPackRelease:
    pack_id: str
    product_id: str
    version: str
    platform: str
    artifact_key: str
    sha256: str
    size_bytes: int
    required_core_version: str = ""

    def __post_init__(self):
        if not self.pack_id or not self.product_id or not _VERSION.fullmatch(self.version):
            raise ValueError("invalid content pack identity/version")
        if not self.artifact_key or self.artifact_key.startswith("/") or ".." in self.artifact_key.split("/"):
            raise ValueError("invalid content pack artifact key")
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ValueError("invalid content pack checksum")
        if self.size_bytes < 0:
            raise ValueError("invalid content pack size")

class ContentManifestRegistry:
    def __init__(self, releases: tuple[ContentPackRelease, ...] = ()):
        self._releases = {(r.product_id, r.pack_id, r.version): r for r in releases}

    def get(self, product_id: str, pack_id: str, version: str | None = None):
        candidates = [r for (p, k, _), r in self._releases.items() if p == product_id and k == pack_id]
        if version is not None:
            return self._releases.get((product_id, pack_id, version))
        return max(candidates, key=lambda r: r.version) if candidates else None

    def for_product(self, product_id: str):
        return tuple(sorted((r for (p, _, _), r in self._releases.items() if p == product_id), key=lambda r: (r.pack_id, r.version), reverse=False))

    def add(self, release: ContentPackRelease):
        self._releases[(release.product_id, release.pack_id, release.version)] = release
