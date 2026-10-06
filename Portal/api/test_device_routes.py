import pytest
from fastapi.testclient import TestClient

from main import Account, AccessSession, Base, Device, Entitlement, engine
from passwords import hash_password
from main import app
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = Account(id="account-device-test", email="device@example.com", password_hash=hash_password("StrongPassword123!"))
        session = AccessSession(id="session-device-test", account_id=account.id, active=True)
        entitlement = Entitlement(id="entitlement-device-test", account_id=account.id, product_id="yow-core", active=True)
        db.add_all([account, session, entitlement])
        db.commit()
    yield
    Base.metadata.drop_all(engine)


def test_bind_requires_product_entitlement():
    client = TestClient(app)
    response = client.post(
        "/v1/devices/bind",
        headers={"X-Session-ID": "session-device-test"},
        json={"account_id": "account-device-test", "device_id": "device-12345678", "product_id": "yow-core"},
    )
    assert response.status_code == 200


def test_bind_rejects_account_without_product_entitlement():
    with Session(engine) as db:
        db.add(Entitlement(id="other-entitlement", account_id="other-account", product_id="yow-core", active=True))
        db.commit()
    client = TestClient(app)
    response = client.post(
        "/v1/devices/bind",
        headers={"X-Session-ID": "session-device-test"},
        json={"account_id": "account-device-test", "device_id": "device-87654321", "product_id": "missing-product"},
    )
    assert response.status_code == 403


def test_list_and_revoke_device_blocks_download_token():
    client = TestClient(app)
    bind = client.post(
        "/v1/devices/bind",
        headers={"X-Session-ID": "session-device-test"},
        json={"account_id": "account-device-test", "device_id": "device-abcdef12", "product_id": "yow-core"},
    )
    assert bind.status_code == 200

    listed = client.get(
        "/v1/devices",
        params={"account_id": "account-device-test"},
        headers={"X-Session-ID": "session-device-test"},
    )
    assert listed.status_code == 200
    assert listed.json()["devices"][0]["device_id"] == "device-abcdef12"
    assert listed.json()["devices"][0]["active"] is True

    revoked = client.post(
        "/v1/devices/revoke",
        params={"account_id": "account-device-test", "device_id": "device-abcdef12"},
        headers={"X-Session-ID": "session-device-test"},
    )
    assert revoked.status_code == 200

    token = client.post(
        "/v1/download-token",
        params={"account_id": "account-device-test", "product_id": "yow-core", "device_id": "device-abcdef12"},
        headers={"X-Session-ID": "session-device-test"},
    )
    assert token.status_code == 403


def test_device_management_rejects_other_account_session():
    client = TestClient(app)
    response = client.get(
        "/v1/devices",
        params={"account_id": "someone-else"},
        headers={"X-Session-ID": "session-device-test"},
    )
    assert response.status_code == 403
