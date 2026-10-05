import hashlib
import hmac
import json

import pytest

from payment_webhook_service import WebhookValidationError, parse_signed_webhook


SECRET = "test-webhook-secret"


def signed(payload: dict) -> tuple[bytes, str]:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    signature = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return raw, signature


def test_valid_exact_body_is_accepted():
    raw, signature = signed({"provider": "test", "status": "paid"})
    assert parse_signed_webhook(raw, signature, SECRET)["status"] == "paid"


def test_tampered_body_is_rejected():
    raw, signature = signed({"provider": "test", "status": "paid"})
    tampered = raw.replace(b'"paid"', b'"refunded"')
    with pytest.raises(WebhookValidationError, match="invalid provider signature"):
        parse_signed_webhook(tampered, signature, SECRET)


def test_missing_signature_is_rejected():
    raw, _ = signed({"provider": "test", "status": "paid"})
    with pytest.raises(WebhookValidationError, match="missing provider signature"):
        parse_signed_webhook(raw, None, SECRET)


def test_missing_secret_is_rejected():
    raw, signature = signed({"provider": "test", "status": "paid"})
    with pytest.raises(WebhookValidationError, match="webhook secret is not configured"):
        parse_signed_webhook(raw, signature, "")


def test_invalid_json_is_rejected_after_signature_verification():
    raw = b'{"provider":"test",'
    signature = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    with pytest.raises(WebhookValidationError, match="invalid webhook JSON"):
        parse_signed_webhook(raw, signature, SECRET)


def test_non_object_json_is_rejected():
    raw = b'["not-an-object"]'
    signature = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    with pytest.raises(WebhookValidationError, match="payload must be an object"):
        parse_signed_webhook(raw, signature, SECRET)
