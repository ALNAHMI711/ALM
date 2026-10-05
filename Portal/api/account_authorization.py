"""Authorization rules for account-scoped portal operations."""

from __future__ import annotations


class AuthorizationError(ValueError):
    """Raised when an authenticated session cannot access a resource."""


def require_same_account(authenticated_account_id: str | None, requested_account_id: str) -> None:
    if not authenticated_account_id:
        raise AuthorizationError("authentication required")
    if authenticated_account_id != requested_account_id:
        raise AuthorizationError("account does not match session")


def require_device_owner(
    authenticated_account_id: str | None,
    device_account_id: str | None,
    device_active: bool,
) -> None:
    if not authenticated_account_id:
        raise AuthorizationError("authentication required")
    if device_account_id != authenticated_account_id or not device_active:
        raise AuthorizationError("device not available")
