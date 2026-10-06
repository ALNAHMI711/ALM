import hashlib
import hmac

import pytest

from download_http_service import authorize_download_request
from download_service import DownloadServiceError
from storage_signer import HmacStorageSigner


def token(account_id, product_id, device_id, expires_at, secret):
    payload = f"{account_id}:{product_id}:{device_id}:{expires_at}"
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{expires_at}.{digest}"


def test_authorized_request_returns_short_lived_signed_location():
    secret = "secret"
    result = authorize_download_request(
        token=token("acct-12345678", "yow-core", "device-12345678", 5000, secret),
        account_id="acct-12345678",
        product_id="yow-core",
        device_id="device-12345678",
        signing_secret=secret,
        entitlement_active=True,
        device_owner="acct-12345678",
        device_active=True,
        storage_key="releases/yow-core.apk",
        storage_signer=HmacStorageSigner("https://gateway.example", "gateway-secret"),
        now=4000,
    )

    assert result.product_id == "yow-core"
    assert result.download_url.startswith("https://gateway.example/releases/yow-core.apk?")
    assert result.expires_at == 4300


def test_missing_storage_key_is_denied():
    secret = "secret"
    with pytest.raises(DownloadServiceError, match="paid artifact unavailable"):
        authorize_download_request(
            token=token("acct-12345678", "yow-core", "device-12345678", 5000, secret),
            account_id="acct-12345678",
            product_id="yow-core",
            device_id="device-12345678",
            signing_secret=secret,
            entitlement_active=True,
            device_owner="acct-12345678",
            device_active=True,
            storage_key=None,
            storage_signer=HmacStorageSigner("https://gateway.example", "gateway-secret"),
            now=4000,
        )
