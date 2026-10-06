from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import main
from product_artifacts import ProductArtifact
from storage_signer import HmacStorageSigner


def test_http_download_enforces_session_entitlement_and_device(monkeypatch, tmp_path):
    db_path = tmp_path / "test.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    main.Base.metadata.create_all(engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SECRET", "test-signing-secret")
    monkeypatch.setattr(main, "ARTIFACT_REGISTRY", main.ProductArtifactRegistry((ProductArtifact("yow-core", "android", "0.1.0", "releases/yow-core.apk"),)))
    monkeypatch.setattr(main, "STORAGE_SIGNER", HmacStorageSigner("https://gateway.example", "gateway-secret"))

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
    assert response.json()["download_url"].startswith("https://gateway.example/releases/yow-core.apk?")
    assert "expires=" in response.json()["download_url"]
    assert "signature=" in response.json()["download_url"]

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
    monkeypatch.setattr(main, "ARTIFACT_REGISTRY", main.ProductArtifactRegistry())

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


def _signed_webhook(payload: dict, secret: str) -> tuple[str, str]:
    import hashlib
    import hmac
    import json

    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    signature = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return raw.decode(), signature


def test_http_webhook_grants_entitlement_and_is_idempotent(monkeypatch, tmp_path):
    db_path = tmp_path / "test-webhook.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    main.Base.metadata.create_all(engine)
    monkeypatch.setattr(main, "engine", engine)
    secret = "test-payment-webhook-secret"
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", secret)

    client = TestClient(main.app)
    payload = {
        "provider": "test",
        "provider_event_id": "evt-paid-12345678",
        "account_id": "acct-webhook-12345678",
        "order_id": "order-webhook-12345678",
        "product_id": "yow-core",
        "amount_minor": 990,
        "currency": "USD",
        "status": "paid",
    }
    body, signature = _signed_webhook(payload, secret)

    response = client.post(
        "/v1/payments/webhook",
        content=body,
        headers={"X-Provider-Signature": signature},
    )
    assert response.status_code == 200
    assert response.json()["entitlement_granted"] is True

    replay = client.post(
        "/v1/payments/webhook",
        content=body,
        headers={"X-Provider-Signature": signature},
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent"] is True

    with Session(engine) as db:
        order = db.get(main.Order, payload["order_id"])
        entitlement = db.scalar(
            select(main.Entitlement).where(
                main.Entitlement.account_id == payload["account_id"],
                main.Entitlement.product_id == payload["product_id"],
            )
        )
        assert order.status == "paid"
        assert entitlement is not None
        assert entitlement.active is True


def test_http_webhook_rejects_existing_order_identity_mismatch(monkeypatch, tmp_path):
    db_path = tmp_path / "test-webhook-mismatch.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    main.Base.metadata.create_all(engine)
    monkeypatch.setattr(main, "engine", engine)
    secret = "test-payment-webhook-secret"
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", secret)

    with Session(engine) as db:
        db.add(main.Order(
            id="order-fixed-12345678",
            account_id="acct-owner-12345678",
            product_id="yow-core",
            amount_minor=990,
            currency="USD",
            status="pending",
        ))
        db.commit()

    client = TestClient(main.app)
    payload = {
        "provider": "test",
        "provider_event_id": "evt-mismatch-12345678",
        "account_id": "acct-attacker-12345678",
        "order_id": "order-fixed-12345678",
        "product_id": "yow-core",
        "amount_minor": 990,
        "currency": "USD",
        "status": "paid",
    }
    body, signature = _signed_webhook(payload, secret)
    response = client.post(
        "/v1/payments/webhook",
        content=body,
        headers={"X-Provider-Signature": signature},
    )
    assert response.status_code == 409

    with Session(engine) as db:
        order = db.get(main.Order, payload["order_id"])
        assert order.account_id == "acct-owner-12345678"
        assert db.scalar(select(main.Entitlement)) is None


def test_http_webhook_refund_deactivates_matching_entitlement(monkeypatch, tmp_path):
    db_path = tmp_path / "test-webhook-refund.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    main.Base.metadata.create_all(engine)
    monkeypatch.setattr(main, "engine", engine)
    secret = "test-payment-webhook-secret"
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", secret)

    with Session(engine) as db:
        db.add(main.Order(
            id="order-refund-12345678",
            account_id="acct-refund-12345678",
            product_id="yow-core",
            amount_minor=990,
            currency="USD",
            status="paid",
        ))
        db.add(main.Entitlement(
            id="ent-refund-12345678",
            account_id="acct-refund-12345678",
            product_id="yow-core",
            active=True,
        ))
        db.commit()

    client = TestClient(main.app)
    payload = {
        "provider": "test",
        "provider_event_id": "evt-refund-12345678",
        "account_id": "acct-refund-12345678",
        "order_id": "order-refund-12345678",
        "product_id": "yow-core",
        "amount_minor": 990,
        "currency": "USD",
        "status": "refunded",
    }
    body, signature = _signed_webhook(payload, secret)
    response = client.post(
        "/v1/payments/webhook",
        content=body,
        headers={"X-Provider-Signature": signature},
    )
    assert response.status_code == 200

    with Session(engine) as db:
        order = db.get(main.Order, payload["order_id"])
        entitlement = db.get(main.Entitlement, "ent-refund-12345678")
        assert order.status == "refunded"
        assert entitlement.active is False


def test_http_webhook_rejects_refund_without_existing_order(monkeypatch, tmp_path):
    db_path = tmp_path / "test-webhook-refund-missing.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}")
    main.Base.metadata.create_all(engine)
    monkeypatch.setattr(main, "engine", engine)
    secret = "test-payment-webhook-secret"
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", secret)

    client = TestClient(main.app)
    payload = {
        "provider": "test",
        "provider_event_id": "evt-refund-missing-12345678",
        "account_id": "acct-refund-12345678",
        "order_id": "order-missing-12345678",
        "product_id": "yow-core",
        "amount_minor": 990,
        "currency": "USD",
        "status": "refunded",
    }
    body, signature = _signed_webhook(payload, secret)
    response = client.post(
        "/v1/payments/webhook",
        content=body,
        headers={"X-Provider-Signature": signature},
    )
    assert response.status_code == 409
