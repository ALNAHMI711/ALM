import pytest

from account_authorization import AuthorizationError, require_device_owner, require_same_account


def test_same_account_is_allowed():
    require_same_account("account-a", "account-a")


def test_missing_session_is_rejected():
    with pytest.raises(AuthorizationError, match="authentication required"):
        require_same_account(None, "account-a")


def test_cross_account_access_is_rejected():
    with pytest.raises(AuthorizationError, match="does not match"):
        require_same_account("account-a", "account-b")


def test_active_owned_device_is_allowed():
    require_device_owner("account-a", "account-a", True)


def test_device_owned_by_other_account_is_rejected():
    with pytest.raises(AuthorizationError, match="device not available"):
        require_device_owner("account-a", "account-b", True)


def test_inactive_device_is_rejected():
    with pytest.raises(AuthorizationError, match="device not available"):
        require_device_owner("account-a", "account-a", False)


def test_missing_session_cannot_bind_or_use_device():
    with pytest.raises(AuthorizationError, match="authentication required"):
        require_device_owner(None, "account-a", True)
