def test_download_token_route_requires_session_header():
    from main import app
    route = next(r for r in app.routes if getattr(r, "path", None) == "/v1/download-token")
    params = {p.name for p in route.dependant.header_params}
    assert "x_session_id" in params


def test_session_account_rejects_missing_session():
    from fastapi import HTTPException
    from main import session_account

    try:
        session_account("missing-session")
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("missing session was accepted")
