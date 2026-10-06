from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import main


def test_http_download_enforces_session_entitlement_and_device(monkeypatch, tmp_path):
    db_path = tmp_path / "test.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    main.Base.metadata.create_all(engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SECRET", "test-signing-secret")
    monkeypatch.setattr(main, "ARTIFACT_URLS", {"yow-core": "https://storage.example/yow-core.apk"})

    client = TestClient(main.app)
    password = "a-strong-password-123"
    email = "http-test@example.com"

    registered = client.post("/v1/accounts/register", json={"email": email, "password": password})
    assert registered.status_code == 200
    account_id = registered.json()["account_id"]

    logged = client.post("/v1/accounts/login", json={"email": email, "password": password})
    assert logged.status_code == 200
    session_id = logged.json()["session_id"]
    device_id = "device-http-12345678"

    with Session(engine) as db:
        db.add(main.Entitlement(id="ent-http", account_id=account_id, product_id="yow-core", active=True))
        db.add(main.Device(id=device_id, account_id=account_id, active=True))
        db.commit()

    token_response = client.post(
        "/v1/download-token",
        params={"account_id": account_id, "product_id": "yow-core", "device_id": device_id},
        headers={"X-Session-ID": session_id},
    )
    assert token_response.status_code == 200

    response = client.get(
        "/v1/download",
        params={"account_id": account_id, "product_id": "yow-core", "device_id": device_id},
        headers={"X-Session-ID": session_id, "X-Download-Token": token_response.json()["token"]},
    )
    assert response.status_code == 200
    assert response.json()["download_url"] == "https://storage.example/yow-core.apk"

    missing_session = client.get(
        "/v1/download",
        params={"account_id": account_id, "product_id": "yow-core", "device_id": device_id},
        headers={"X-Download-Token": token_response.json()["token"]},
    )
    assert missing_session.status_code == 401

    other_device = client.get(
        "/v1/download",
        params={"account_id": account_id, "product_id": "yow-core", "device_id": "device-other-12345678"},
        headers={"X-Session-ID": session_id, "X-Download-Token": token_response.json()["token"]},
    )
    assert other_device.status_code == 403


def test_http_download_denies_without_artifact(monkeypatch, tmp_path):
    db_path = tmp_path / "test-no-artifact.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    main.Base.metadata.create_all(engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SECRET", "test-signing-secret")
    monkeypatch.setattr(main, "ARTIFACT_URLS", {})

    client = TestClient(main.app)
    account_id = "acct-no-artifact-12345678"
    device_id = "device-no-artifact-12345678"
    session_id = "session-no-artifact-12345678"
    with Session(engine) as db:
        db.add(main.Account(id=account_id, email="no-artifact@example.com", password_hash=main.hash_password("another-strong-password-123")))
        db.add(main.AccessSession(id=session_id, account_id=account_id, active=True))
        db.add(main.Entitlement(id="ent-no-artifact", account_id=account_id, product_id="yow-core", active=True))
        db.add(main.Device(id=device_id, account_id=account_id, active=True))
        db.commit()

    expires = int(main.time.time()) + 300
    token = main.sign_token(account_id, "yow-core", device_id, expires)
    response = client.get(
        "/v1/download",
        params={"account_id": account_id, "product_id": "yow-core", "device_id": device_id},
        headers={"X-Session-ID": session_id, "X-Download-Token": token},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "paid artifact unavailable"
