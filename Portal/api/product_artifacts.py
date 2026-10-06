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
    storage_url: str


class ProductArtifactRegistry:
    def __init__(self, artifacts: tuple[ProductArtifact, ...] = ()):
        self._artifacts = {item.product_id: item for item in artifacts}

    def get(self, product_id: str) -> ProductArtifact | None:
        return self._artifacts.get(product_id)

    def add(self, artifact: ProductArtifact) -> None:
        if not artifact.product_id or not artifact.storage_url:
            raise ValueError("invalid artifact")
        self._artifacts[artifact.product_id] = artifact
