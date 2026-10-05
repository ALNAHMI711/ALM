from auth_routes import is_valid_account_id, normalize_email


def test_normalize_email():
    assert normalize_email("  USER@Example.COM ") == "user@example.com"


def test_normalize_email_rejects_invalid():
    try:
        normalize_email("not-an-email")
    except ValueError:
        return
    raise AssertionError("invalid email accepted")


def test_account_id_validation():
    assert is_valid_account_id("account-1234")
    assert not is_valid_account_id("a")
    assert not is_valid_account_id("bad id")
