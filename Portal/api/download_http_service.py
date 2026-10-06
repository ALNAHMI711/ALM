"""HTTP-facing paid download contract."""

from __future__ import annotations

from dataclasses import dataclass

from download_service import Artifact, DownloadServiceError, authorize_download
from storage_signer import StorageSigner


@dataclass(frozen=True)
class DownloadResponse:
    product_id: str
    download_url: str
    expires_at: int


def authorize_download_request(
    *,
    token: str,
    account_id: str,
    product_id: str,
    device_id: str,
    signing_secret: str,
    entitlement_active: bool,
    device_owner: str | None,
    device_active: bool,
    storage_key: str | None,
    storage_signer: StorageSigner,
    storage_url_ttl: int = 300,
    now: int | None = None,
) -> DownloadResponse:
    artifact = Artifact(product_id=product_id, storage_key=storage_key) if storage_key else None

    authorized = authorize_download(
        token=token,
        account_id=account_id,
        product_id=product_id,
        device_id=device_id,
        signing_secret=signing_secret,
        entitlement_active=entitlement_active,
        device_owner=device_owner,
        device_active=device_active,
        artifact=artifact,
        storage_signer=storage_signer,
        storage_url_ttl=storage_url_ttl,
        now=now,
    )

    return DownloadResponse(
        product_id=product_id,
        download_url=authorized.url,
        expires_at=authorized.expires_at,
    )
