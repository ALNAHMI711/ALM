from auth_routes import is_valid_account_id, normalize_email


def test_account_id_accepts_generated_style_ids():
    assert is_valid_account_id("VjQ7Qn7k-account-01")


def test_account_id_rejects_whitespace():
    assert not is_valid_account_id("account 01")


def test_email_normalization_is_deterministic():
    assert normalize_email(" User@Example.com ") == "user@example.com"
