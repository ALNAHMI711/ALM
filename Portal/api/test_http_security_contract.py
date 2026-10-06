import ast
from pathlib import Path


MAIN = Path(__file__).with_name("main.py")


def _function(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)


def test_sensitive_routes_have_session_parameters():
    source = MAIN.read_text(encoding="utf-8")
    assert 'def bind_device(req: DeviceBind, x_session_id: str | None = Header' in source
    assert 'def account_profile(account_id: str, x_session_id: str | None = Header' in source
    assert 'def revoke_session(session_id: str, x_session_id: str | None = Header' in source


def test_webhook_reads_raw_body_before_signed_parser():
    source = MAIN.read_text(encoding="utf-8")
    body_pos = source.index("raw_body = await request.body()")
    parser_pos = source.index("parse_signed_webhook(", body_pos)
    assert body_pos < parser_pos


def test_webhook_requires_configured_secret():
    source = MAIN.read_text(encoding="utf-8")
    assert 'if not secret:' in source
    assert 'status_code=503' in source
