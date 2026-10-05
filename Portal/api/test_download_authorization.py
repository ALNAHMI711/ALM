import pytest


def test_download_token_requires_session():
    import main

    with pytest.raises(main.HTTPException) as exc:
        main.download_token(
            account_id="account-1234",
            product_id="yow-core",
            device_id="device-1234",
            x_session_id=None,
        )
    assert exc.value.status_code == 401


def test_download_token_rejects_account_session_mismatch(monkeypatch):
    import main

    monkeypatch.setattr(main, "session_account", lambda session_id: "owner-account")
    with pytest.raises(main.HTTPException) as exc:
        main.download_token(
            account_id="different-account",
            product_id="yow-core",
            device_id="device-1234",
            x_session_id="valid-session",
        )
    assert exc.value.status_code == 403


def test_download_token_checks_entitlement_after_authentication(monkeypatch):
    import main

    monkeypatch.setattr(main, "session_account", lambda session_id: "owner-account")
    with pytest.raises(main.HTTPException) as exc:
        main.download_token(
            account_id="owner-account",
            product_id="yow-core",
            device_id="device-1234",
            x_session_id="valid-session",
        )
    assert exc.value.status_code == 403
