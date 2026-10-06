import hashlib
import hmac
import json

import pytest

from webhook_http_service import parse_payment_webhook


def signature(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_signed_raw_body_is_parsed_after_verification():
    secret = "webhook-secret"
    body = json.dumps({"provider": "test", "status": "paid"}).encode()

    assert parse_payment_webhook(body, signature(body, secret), secret)["status"] == "paid"


def test_tampered_body_is_rejected():
    secret = "webhook-secret"
    original = b'{"provider":"test","status":"paid"}'
    tampered = b'{"provider":"test","status":"refunded"}'

    with pytest.raises(ValueError, match="invalid provider signature"):
        parse_payment_webhook(tampered, signature(original, secret), secret)


def test_missing_signature_is_rejected():
    with pytest.raises(ValueError, match="missing provider signature"):
        parse_payment_webhook(b"{}", None, "webhook-secret")


def test_missing_secret_is_rejected():
    body = b"{}"
    with pytest.raises(ValueError, match="webhook secret is not configured"):
        parse_payment_webhook(body, signature(body, "x"), "")
