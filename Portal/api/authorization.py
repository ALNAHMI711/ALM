"""Authorization helpers for account and device ownership boundaries."""

from __future__ import annotations


class AuthorizationError(ValueError):
    """Raised when a session cannot act on the requested account."""


def require_session_account(
    session_id: str | None,
    requested_account_id: str,
    resolve_account,
) -> str:
    if not session_id:
        raise AuthorizationError("session required")
    authenticated_account_id = resolve_account(session_id)
    if authenticated_account_id != requested_account_id:
        raise AuthorizationError("account does not match session")
    return authenticated_account_id


def require_device_owner(
    device_account_id: str | None,
    requested_account_id: str,
    active: bool,
) -> None:
    if device_account_id != requested_account_id or not active:
        raise AuthorizationError("device not available")
