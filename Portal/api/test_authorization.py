import pytest

from authorization import AuthorizationError, require_device_owner, require_session_account


def resolver(session_id: str) -> str:
    return {"session-a": "account-a"}.get(session_id)


def test_session_owner_is_accepted():
    assert require_session_account("session-a", "account-a", resolver) == "account-a"


def test_missing_session_is_rejected():
    with pytest.raises(AuthorizationError, match="session required"):
        require_session_account(None, "account-a", resolver)


def test_cross_account_session_is_rejected():
    with pytest.raises(AuthorizationError, match="account does not match session"):
        require_session_account("session-a", "account-b", resolver)


def test_unknown_session_is_rejected():
    with pytest.raises(AuthorizationError):
        require_session_account("unknown", "account-a", resolver)


def test_active_owned_device_is_accepted():
    require_device_owner("account-a", "account-a", True)


def test_cross_account_device_is_rejected():
    with pytest.raises(AuthorizationError, match="device not available"):
        require_device_owner("account-b", "account-a", True)


def test_inactive_device_is_rejected():
    with pytest.raises(AuthorizationError, match="device not available"):
        require_device_owner("account-a", "account-a", False)
