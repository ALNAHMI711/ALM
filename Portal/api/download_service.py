"""Server-side authorization for paid artifact downloads."""

from __future__ import annotations

from dataclasses import dataclass

from download_authorization import DownloadAuthorizationError, verify_download_token
from storage_signer import SignedStorageUrl, StorageSigner, StorageSigningError


class DownloadServiceError(ValueError):
    """Raised when a paid artifact cannot be authorized."""


@dataclass(frozen=True)
class Artifact:
    product_id: str
    storage_key: str


def authorize_download(
    *,
    token: str,
    account_id: str,
    product_id: str,
    device_id: str,
    signing_secret: str,
    entitlement_active: bool,
    device_owner: str | None,
    device_active: bool,
    artifact: Artifact | None,
    storage_signer: StorageSigner,
    storage_url_ttl: int = 300,
    now: int | None = None,
) -> SignedStorageUrl:
    try:
        verify_download_token(
            token,
            account_id,
            product_id,
            device_id,
            signing_secret,
            now=now,
        )
    except DownloadAuthorizationError as exc:
        raise DownloadServiceError(str(exc)) from exc

    if not entitlement_active:
        raise DownloadServiceError("active entitlement required")
    if device_owner != account_id or not device_active:
        raise DownloadServiceError("active bound device required")
    if artifact is None or artifact.product_id != product_id or not artifact.storage_key:
        raise DownloadServiceError("paid artifact unavailable")

    try:
        return storage_signer.sign(
            artifact_key=artifact.storage_key,
            expires_in=storage_url_ttl,
            now=now,
        )
    except StorageSigningError as exc:
        raise DownloadServiceError("signed artifact unavailable") from exc
