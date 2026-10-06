from storage_signer import HmacStorageSigner
from storage_verifier import verify_hmac_storage_url


def test_gateway_contract_accepts_valid_signed_url():
    result = HmacStorageSigner("https://cdn.example/download", "secret").sign(
        artifact_key="releases/yow-core.apk", expires_in=300, now=1000
    )
    assert verify_hmac_storage_url(result.url, secret="secret", now=1001)


def test_gateway_contract_rejects_expired_url():
    result = HmacStorageSigner("https://cdn.example/download", "secret").sign(
        artifact_key="releases/yow-core.apk", expires_in=300, now=1000
    )
    assert not verify_hmac_storage_url(result.url, secret="secret", now=1300)


def test_gateway_contract_rejects_tampered_signature():
    result = HmacStorageSigner("https://cdn.example/download", "secret").sign(
        artifact_key="releases/yow-core.apk", expires_in=300, now=1000
    )
    tampered = result.url.replace("signature=", "signature=bad")
    assert not verify_hmac_storage_url(tampered, secret="secret", now=1001)


def test_gateway_contract_rejects_wrong_secret():
    result = HmacStorageSigner("https://cdn.example/download", "secret").sign(
        artifact_key="releases/yow-core.apk", expires_in=300, now=1000
    )
    assert not verify_hmac_storage_url(result.url, secret="wrong", now=1001)


def test_gateway_contract_rejects_missing_parameters():
    assert not verify_hmac_storage_url(
        "https://cdn.example/download/releases/yow-core.apk",
        secret="secret",
        now=1001,
    )
