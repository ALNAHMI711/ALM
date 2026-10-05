"""Provider-agnostic payment webhook validation.

The service validates the exact request body before parsing business fields.
HTTP/framework wiring stays in main.py so the security contract can be tested
without relying on request serialization behavior.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


class WebhookValidationError(ValueError):
    """Raised when a payment webhook cannot be trusted or parsed."""


def validate_signature(raw_body: bytes, signature: str | None, secret: str) -> None:
    if not signature:
        raise WebhookValidationError("missing provider signature")
    if not secret:
        raise WebhookValidationError("webhook secret is not configured")
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature.strip(), expected):
        raise WebhookValidationError("invalid provider signature")


def parse_signed_webhook(
    raw_body: bytes,
    signature: str | None,
    secret: str,
) -> dict[str, Any]:
    """Verify the exact body, then parse a JSON object.

    Parsing is deliberately performed only after signature verification.
    """
    validate_signature(raw_body, signature, secret)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookValidationError("invalid webhook JSON") from exc
    if not isinstance(payload, dict):
        raise WebhookValidationError("webhook payload must be an object")
    return payload
