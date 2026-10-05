"""Server-side authorization for paid artifact downloads.

The service never trusts a client-supplied storage URL. A caller must present a
valid short-lived token and the database must still show an active entitlement
and active device before an artifact URL is returned.
"""

from __future__ import annotations

from dataclasses import dataclass

from download_authorization import DownloadAuthorizationError, verify_download_token


class DownloadServiceError(ValueError):
    """Raised when a paid artifact cannot be authorized."""


@dataclass(frozen=True)
class Artifact:
    product_id: str
    storage_url: str


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
    now: int | None = None,
) -> Artifact:
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
    if artifact is None or artifact.product_id != product_id or not artifact.storage_url:
        raise DownloadServiceError("paid artifact unavailable")

    return artifact
