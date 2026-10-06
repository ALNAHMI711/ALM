"""Short-lived authorization tokens for versioned content-pack downloads."""
from __future__ import annotations
import hashlib
import hmac
import time

class ContentDownloadAuthorizationError(ValueError):
    pass

def sign_content_token(account_id: str, product_id: str, device_id: str, pack_id: str, version: str, expires_at: int, secret: str) -> str:
    if not secret:
        raise ContentDownloadAuthorizationError("signing secret required")
    payload = f"{account_id}:{product_id}:{device_id}:{pack_id}:{version}:{expires_at}"
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{expires_at}.{digest}"

def verify_content_token(token: str, account_id: str, product_id: str, device_id: str, pack_id: str, version: str, secret: str, now: int | None = None) -> None:
    try:
        expires_raw, signature = token.split(".", 1)
        expires_at = int(expires_raw)
    except (ValueError, AttributeError):
        raise ContentDownloadAuthorizationError("invalid content download token")
    current = int(time.time()) if now is None else int(now)
    if expires_at <= current:
        raise ContentDownloadAuthorizationError("content download token expired")
    expected = sign_content_token(account_id, product_id, device_id, pack_id, version, expires_at, secret).split(".", 1)[1]
    if not hmac.compare_digest(signature, expected):
        raise ContentDownloadAuthorizationError("invalid content download token")
