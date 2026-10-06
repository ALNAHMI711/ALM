import pytest

from storage_signer import HmacStorageSigner, StorageSigningError


def test_hmac_signer_returns_expiring_gateway_url():
    signer = HmacStorageSigner("https://cdn.example/download", "secret")
    result = signer.sign(artifact_key="releases/yow-core.apk", expires_in=300, now=1000)

    assert result.expires_at == 1300
    assert result.url.startswith("https://cdn.example/download/releases/yow-core.apk?")
    assert "expires=1300" in result.url
    assert "signature=" in result.url


def test_hmac_signer_rejects_unconfigured_gateway():
    with pytest.raises(StorageSigningError):
        HmacStorageSigner("", "secret").sign(artifact_key="file.apk", expires_in=300, now=1000)


def test_hmac_signer_rejects_non_https_gateway():
    with pytest.raises(StorageSigningError):
        HmacStorageSigner("http://cdn.example", "secret").sign(artifact_key="file.apk", expires_in=300, now=1000)


def test_hmac_signer_rejects_invalid_ttl():
    with pytest.raises(StorageSigningError):
        HmacStorageSigner("https://cdn.example", "secret").sign(artifact_key="file.apk", expires_in=0, now=1000)
