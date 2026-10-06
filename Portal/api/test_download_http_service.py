import hashlib
import hmac

import pytest

from download_http_service import authorize_download_request
from download_service import DownloadServiceError


def token(account_id, product_id, device_id, expires_at, secret):
    payload = f"{account_id}:{product_id}:{device_id}:{expires_at}"
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{expires_at}.{digest}"


def test_authorized_request_returns_private_artifact_location():
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
        storage_url="https://private-storage.example/yow-core.apk",
        now=4000,
    )

    assert result.product_id == "yow-core"
    assert result.storage_url.startswith("https://")


def test_missing_storage_location_is_denied():
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
            storage_url=None,
            now=4000,
        )
