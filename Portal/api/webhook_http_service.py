"""HTTP-independent webhook processing contract.

The HTTP adapter must provide the exact raw request body and signature. This
module verifies the body before deserializing it into business data.
"""

from __future__ import annotations

from payment_webhook_service import WebhookValidationError, parse_signed_webhook


def parse_payment_webhook(raw_body: bytes, signature: str | None, secret: str) -> dict:
    try:
        return parse_signed_webhook(raw_body, signature, secret)
    except WebhookValidationError as exc:
        raise ValueError(str(exc)) from exc
