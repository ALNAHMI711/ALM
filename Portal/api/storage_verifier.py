"""Verification contract for HMAC storage gateway URLs.

This helper is for contract tests and gateway implementations. Portal
entitlement authorization remains a separate concern.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import parse_qs, urlsplit


def verify_hmac_storage_url(url: str, *, secret: str, now: int | None = None) -> bool:
    if not secret or not url.startswith("https://"):
        return False
    parsed = urlsplit(url)
    values = parse_qs(parsed.query, strict_parsing=False)
    expires = values.get("expires", [])
    signatures = values.get("signature", [])
    if len(expires) != 1 or len(signatures) != 1:
        return False
    try:
        expires_at = int(expires[0])
    except ValueError:
        return False
    current = int(time.time()) if now is None else int(now)
    if expires_at <= current:
        return False
    canonical = f"{parsed.path}:{expires_at}"
    expected = hmac.new(
        secret.encode(), canonical.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signatures[0], expected)
