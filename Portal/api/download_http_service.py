"""HTTP-facing paid download contract.

The route adapter can use this service to authorize a token and resolve the
approved artifact. It deliberately returns metadata rather than a public,
permanent download URL.
"""

from __future__ import annotations

from dataclasses import dataclass

from download_service import Artifact, DownloadServiceError, authorize_download


@dataclass(frozen=True)
class DownloadResponse:
    product_id: str
    storage_url: str


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
    storage_url: str | None,
    now: int | None = None,
) -> DownloadResponse:
    artifact = None
    if storage_url:
        artifact = Artifact(product_id=product_id, storage_url=storage_url)

    try:
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
            now=now,
        )
    except DownloadServiceError:
        raise

    return DownloadResponse(
        product_id=authorized.product_id,
        storage_url=authorized.storage_url,
    )
