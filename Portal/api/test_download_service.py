import hashlib
import hmac

import pytest

from download_service import Artifact, DownloadServiceError, authorize_download
from storage_signer import HmacStorageSigner


SECRET = "test-secret"


def make_token(account_id, product_id, device_id, expires_at, secret):
    payload = f"{account_id}:{product_id}:{device_id}:{expires_at}"
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{expires_at}.{digest}"


def signer():
    return HmacStorageSigner("https://gateway.example", "gateway-secret")


def test_authorizes_only_active_entitlement_and_owned_device():
    result = authorize_download(
        token=make_token("acct-12345678", "yow-core", "device-12345678", 2000, SECRET),
        account_id="acct-12345678",
        product_id="yow-core",
        device_id="device-12345678",
        signing_secret=SECRET,
        entitlement_active=True,
        device_owner="acct-12345678",
        device_active=True,
        artifact=Artifact("yow-core", "releases/yow-core.apk"),
        storage_signer=signer(),
        now=1000,
    )

    assert result.url.startswith("https://gateway.example/releases/yow-core.apk?")
    assert result.expires_at == 1300


@pytest.mark.parametrize(
    "entitlement_active,device_owner,device_active,artifact",
    [
        (False, "acct-12345678", True, Artifact("yow-core", "releases/yow-core.apk")),
        (True, "other-account", True, Artifact("yow-core", "releases/yow-core.apk")),
        (True, "acct-12345678", False, Artifact("yow-core", "releases/yow-core.apk")),
        (True, "acct-12345678", True, None),
    ],
)
def test_rejects_missing_runtime_requirements(entitlement_active, device_owner, device_active, artifact):
    with pytest.raises(DownloadServiceError):
        authorize_download(
            token=make_token("acct-12345678", "yow-core", "device-12345678", 2000, SECRET),
            account_id="acct-12345678",
            product_id="yow-core",
            device_id="device-12345678",
            signing_secret=SECRET,
            entitlement_active=entitlement_active,
            device_owner=device_owner,
            device_active=device_active,
            artifact=artifact,
            storage_signer=signer(),
            now=1000,
        )


def test_token_cannot_authorize_another_product():
    with pytest.raises(DownloadServiceError):
        authorize_download(
            token=make_token("acct-12345678", "yow-core", "device-12345678", 2000, SECRET),
            account_id="acct-12345678",
            product_id="different-product",
            device_id="device-12345678",
            signing_secret=SECRET,
            entitlement_active=True,
            device_owner="acct-12345678",
            device_active=True,
            artifact=Artifact("different-product", "releases/other.apk"),
            storage_signer=signer(),
            now=1000,
        )


def test_storage_signing_failure_does_not_return_permanent_location():
    with pytest.raises(DownloadServiceError, match="signed artifact unavailable"):
        authorize_download(
            token=make_token("acct-12345678", "yow-core", "device-12345678", 2000, SECRET),
            account_id="acct-12345678",
            product_id="yow-core",
            device_id="device-12345678",
            signing_secret=SECRET,
            entitlement_active=True,
            device_owner="acct-12345678",
            device_active=True,
            artifact=Artifact("yow-core", "releases/yow-core.apk"),
            storage_signer=HmacStorageSigner("", "gateway-secret"),
            now=1000,
        )
