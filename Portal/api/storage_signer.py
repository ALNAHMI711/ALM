"""Short-lived artifact URL signing abstraction.

The portal authorizes ownership first, then asks a storage signer for a URL
that expires independently of the portal entitlement token. The signer
interface is provider-agnostic; the bundled HMAC implementation is intended
for a storage gateway/CDN that validates the same signature contract.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from urllib.parse import quote, urlencode
from pathlib import PurePosixPath


class StorageSigningError(ValueError):
    """Raised when an artifact cannot receive a signed download URL."""


@dataclass(frozen=True)
class SignedStorageUrl:
    url: str
    expires_at: int


class StorageSigner:
    """Interface implemented by the actual storage/CDN provider adapter."""

    def sign(self, *, artifact_key: str, expires_in: int, now: int | None = None) -> SignedStorageUrl:
        raise NotImplementedError


@dataclass(frozen=True)
class HmacStorageSigner(StorageSigner):
    """Sign URLs for a storage gateway under our control.

    The gateway must independently verify expires and signature using the
    same secret and canonical path. This is not a claim that an arbitrary
    object-store URL accepts these signatures.
    """

    base_url: str
    secret: str

    def sign(self, *, artifact_key: str, expires_in: int, now: int | None = None) -> SignedStorageUrl:
        if not self.base_url.startswith("https://") or not artifact_key:
            raise StorageSigningError("storage signer is not configured")
        key_path = PurePosixPath(artifact_key)
        if key_path.is_absolute() or ".." in key_path.parts:
            raise StorageSigningError("invalid artifact key")
        if expires_in <= 0 or not self.secret:
            raise StorageSigningError("invalid storage signing configuration")

        expires_at = int(time.time()) if now is None else int(now)
        expires_at += expires_in
        encoded_key = quote(artifact_key.lstrip("/"), safe="/._-")
        path = f"/{encoded_key}"
        canonical = f"{path}:{expires_at}"
        signature = hmac.new(
            self.secret.encode(),
            canonical.encode(),
            hashlib.sha256,
        ).hexdigest()
        query = urlencode({"expires": expires_at, "signature": signature})
        return SignedStorageUrl(
            url=f"{self.base_url.rstrip('/')}{path}?{query}",
            expires_at=expires_at,
        )
