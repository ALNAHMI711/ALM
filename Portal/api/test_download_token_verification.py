import hashlib
import hmac

import pytest

from download_authorization import DownloadAuthorizationError, verify_download_token


SECRET = "download-secret"


def token(account: str, product: str, device: str, expires: int) -> str:
    payload = f"{account}:{product}:{device}:{expires}"
    digest = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{expires}.{digest}"


def test_valid_token_is_accepted():
    verify_download_token(
        token("a", "yow-core", "device-123", 2000),
        "a",
        "yow-core",
        "device-123",
        SECRET,
        now=1000,
    )


@pytest.mark.parametrize(
    "account,product,device",
    [
        ("other", "yow-core", "device-123"),
        ("a", "other-product", "device-123"),
        ("a", "yow-core", "other-device"),
    ],
)
def test_token_cannot_be_replayed_for_other_binding(account, product, device):
    original = token("a", "yow-core", "device-123", 2000)
    with pytest.raises(DownloadAuthorizationError, match="invalid download token"):
        verify_download_token(original, account, product, device, SECRET, now=1000)


def test_expired_token_is_rejected():
    with pytest.raises(DownloadAuthorizationError, match="expired"):
        verify_download_token(
            token("a", "yow-core", "device-123", 1000),
            "a",
            "yow-core",
            "device-123",
            SECRET,
            now=1000,
        )


def test_malformed_token_is_rejected():
    with pytest.raises(DownloadAuthorizationError, match="invalid"):
        verify_download_token(
            "not-a-token",
            "a",
            "yow-core",
            "device-123",
            SECRET,
            now=1000,
        )


def test_tampered_signature_is_rejected():
    original = token("a", "yow-core", "device-123", 2000)
    tampered = original[:-1] + ("0" if original[-1] != "0" else "1")
    with pytest.raises(DownloadAuthorizationError, match="invalid"):
        verify_download_token(
            tampered,
            "a",
            "yow-core",
            "device-123",
            SECRET,
            now=1000,
        )
