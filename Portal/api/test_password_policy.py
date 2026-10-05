from passwords import hash_password, verify_password


def test_password_hash_is_not_reversible_text():
    encoded = hash_password("A sufficiently long password")
    assert "A sufficiently long password" not in encoded
    assert encoded.startswith("scrypt$")


def test_password_verification_handles_malformed_hash():
    assert verify_password("anything", "not-a-valid-hash") is False
