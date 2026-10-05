"""Reusable HTTP authorization helpers for account-scoped routes."""

from __future__ import annotations

from fastapi import HTTPException

from account_authorization import require_same_account
from session_service import get_session_account


def require_session_account(db, session_model, session_id: str | None, requested_account_id: str) -> str:
    if not session_id:
        raise HTTPException(status_code=401, detail="جلسة مطلوبة")
    authenticated = get_session_account(db, session_model, session_id)
    try:
        require_same_account(authenticated, requested_account_id)
    except ValueError as exc:
        status = 401 if not authenticated else 403
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return authenticated
