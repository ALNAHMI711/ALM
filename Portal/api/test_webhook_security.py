import hashlib
import hmac

from webhook_security import verify_hmac_sha256


def test_exact_body_signature_is_accepted():
    body = b'{"event":"paid","amount":100}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_sha256(body, signature, secret)


def test_tampered_body_is_rejected():
    body = b'{"event":"paid","amount":100}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert not verify_hmac_sha256(b'{"event":"paid","amount":999}', signature, secret)


def test_missing_signature_or_secret_is_rejected():
    assert not verify_hmac_sha256(b"body", None, "secret")
    assert not verify_hmac_sha256(b"body", "abc", "")
