"""Server-side product-to-artifact registry.

The registry intentionally stores no payment state. Entitlements remain the
source of truth for access; this module only resolves an approved artifact.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductArtifact:
    product_id: str
    platform: str
    version: str
    storage_key: str
    name: str = ""
    kind: str = "game"
    release_id: str = ""

    @property
    def storage_url(self) -> str:
        """Compatibility accessor; paid routes must never return this field."""
        return self.storage_key


class ProductArtifactRegistry:
    def __init__(self, artifacts: tuple[ProductArtifact, ...] = ()):
        self._artifacts: dict[str, dict[str, ProductArtifact]] = {}
        for artifact in artifacts:
            self.add(artifact)

    def get(self, product_id: str, version: str | None = None) -> ProductArtifact | None:
        releases = self._artifacts.get(product_id)
        if not releases:
            return None
        if version is not None:
            return releases.get(version)
        return max(releases.values(), key=lambda item: item.version)

    def versions(self, product_id: str) -> tuple[ProductArtifact, ...]:
        releases = self._artifacts.get(product_id, {})
        return tuple(sorted(releases.values(), key=lambda item: item.version, reverse=True))

    def all(self) -> tuple[ProductArtifact, ...]:
        """Return the latest approved release for each product."""
        return tuple(
            self._artifacts[key][max(self._artifacts[key])]
            for key in sorted(self._artifacts)
        )

    def add(self, artifact: ProductArtifact) -> None:
        if not artifact.product_id or not artifact.storage_key or not artifact.version:
            raise ValueError("invalid artifact")
        self._artifacts.setdefault(artifact.product_id, {})[artifact.version] = artifact
