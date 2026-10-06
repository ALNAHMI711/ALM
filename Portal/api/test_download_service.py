import hashlib
import hmac

import pytest

from download_service import Artifact, DownloadServiceError, authorize_download


def make_token(account_id, product_id, device_id, expires_at, secret):
    payload = f"{account_id}:{product_id}:{device_id}:{expires_at}"
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{expires_at}.{digest}"


def test_authorizes_only_active_entitlement_and_owned_device():
    secret = "test-secret"
    token = make_token("acct-12345678", "yow-core", "device-12345678", 2000, secret)

    artifact = authorize_download(
        token=token,
        account_id="acct-12345678",
        product_id="yow-core",
        device_id="device-12345678",
        signing_secret=secret,
        entitlement_active=True,
        device_owner="acct-12345678",
        device_active=True,
        artifact=Artifact("yow-core", "https://private.example/artifact"),
        now=1000,
    )

    assert artifact.storage_url.startswith("https://")


@pytest.mark.parametrize(
    "entitlement_active,device_owner,device_active,artifact",
    [
        (False, "acct-12345678", True, Artifact("yow-core", "https://private.example/a")),
        (True, "other-account", True, Artifact("yow-core", "https://private.example/a")),
        (True, "acct-12345678", False, Artifact("yow-core", "https://private.example/a")),
        (True, "acct-12345678", True, None),
    ],
)
def test_rejects_missing_runtime_requirements(entitlement_active, device_owner, device_active, artifact):
    secret = "test-secret"
    token = make_token("acct-12345678", "yow-core", "device-12345678", 2000, secret)

    with pytest.raises(DownloadServiceError):
        authorize_download(
            token=token,
            account_id="acct-12345678",
            product_id="yow-core",
            device_id="device-12345678",
            signing_secret=secret,
            entitlement_active=entitlement_active,
            device_owner=device_owner,
            device_active=device_active,
            artifact=artifact,
            now=1000,
        )


def test_token_cannot_authorize_another_product():
    secret = "test-secret"
    token = make_token("acct-12345678", "yow-core", "device-12345678", 2000, secret)

    with pytest.raises(DownloadServiceError):
        authorize_download(
            token=token,
            account_id="acct-12345678",
            product_id="different-product",
            device_id="device-12345678",
            signing_secret=secret,
            entitlement_active=True,
            device_owner="acct-12345678",
            device_active=True,
            artifact=Artifact("different-product", "https://private.example/a"),
            now=1000,
        )


def test_authorize_download_rejects_non_https_artifact():
    import pytest
    with pytest.raises(DownloadServiceError, match="artifact"):
        authorize_download(
            token=_token("acct-12345678", "yow-core", "device-12345678"),
            account_id="acct-12345678",
            product_id="yow-core",
            device_id="device-12345678",
            signing_secret=SECRET,
            entitlement_active=True,
            device_owner="acct-12345678",
            device_active=True,
            artifact=Artifact(product_id="yow-core", storage_url="http://storage.example/file.apk"),
        )
