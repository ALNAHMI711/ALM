"""Payment webhook signature validation helpers.

Providers should sign the exact request body with HMAC-SHA256.
"""

from __future__ import annotations

import hashlib
import hmac


def verify_hmac_sha256(raw_body: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature.strip(), expected)
