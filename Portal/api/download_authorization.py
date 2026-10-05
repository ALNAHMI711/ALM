"""Authorization helpers for short-lived paid-content download tokens."""

from __future__ import annotations

import hashlib
import hmac
import time


class DownloadAuthorizationError(ValueError):
    """Raised when a download token is invalid, expired, or mismatched."""


def verify_download_token(
    token: str,
    account_id: str,
    product_id: str,
    device_id: str,
    secret: str,
    *,
    now: int | None = None,
) -> None:
    if not token or not secret:
        raise DownloadAuthorizationError("invalid download token")

    try:
        expires_text, supplied_digest = token.split(".", 1)
        expires_at = int(expires_text)
    except (ValueError, TypeError):
        raise DownloadAuthorizationError("invalid download token")

    current_time = int(time.time()) if now is None else now
    if expires_at <= current_time:
        raise DownloadAuthorizationError("download token expired")

    payload = f"{account_id}:{product_id}:{device_id}:{expires_at}"
    expected_digest = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(supplied_digest, expected_digest):
        raise DownloadAuthorizationError("invalid download token")
