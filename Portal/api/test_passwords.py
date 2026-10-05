from passwords import hash_password, verify_password


def test_password_round_trip():
    encoded = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)


def test_short_password_rejected():
    try:
        hash_password("short")
    except ValueError:
        return
    raise AssertionError("short password accepted")
