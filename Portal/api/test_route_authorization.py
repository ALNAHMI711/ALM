from fastapi import HTTPException
import pytest

from route_authorization import require_session_account


class SessionRow:
    def __init__(self, account_id: str, active: bool = True):
        self.account_id = account_id
        self.active = active


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    def scalar(self, query):
        # The helper's dependency uses SQLAlchemy select(); emulate lookup by
        # extracting the bound session id from the query is unnecessary here.
        return next(iter(self.rows.values()), None)


def test_missing_session_is_rejected():
    with pytest.raises(HTTPException) as exc:
        require_session_account(None, object(), None, "acct-12345678")
    assert exc.value.status_code == 401


def test_authenticated_account_must_match_requested_account():
    db = FakeSession({"x": SessionRow("other-account")})
    with pytest.raises(HTTPException) as exc:
        require_session_account(db, SessionRow, "x", "acct-12345678")
    assert exc.value.status_code in (401, 403)
