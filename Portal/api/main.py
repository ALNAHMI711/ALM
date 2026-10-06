from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import Boolean, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from fastapi.staticfiles import StaticFiles

from auth_routes import normalize_email
from passwords import hash_password, verify_password
from payment_webhook_service import WebhookValidationError, parse_signed_webhook
from session_service import get_session_account
from download_service import DownloadServiceError, authorize_download, Artifact
from product_artifacts import ProductArtifact, ProductArtifactRegistry

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./yow.db")
SECRET = os.getenv("ENTITLEMENT_SIGNING_SECRET", "")
TOKEN_TTL = 900
ARTIFACT_REGISTRY = ProductArtifactRegistry((ProductArtifact(product_id="yow-core", platform="android", version="0.1.0", storage_url=os.getenv("YOW_CORE_ARTIFACT_URL", "")),))

if not SECRET:
    SECRET = "development-only-change-me"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))


class AccessSession(Base):
    __tablename__ = "access_sessions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(128), index=True)
    product_id: Mapped[str] = mapped_column(String(128), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), default="pending")


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    provider_event_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    order_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32))


class Entitlement(Base):
    __tablename__ = "entitlements"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(128), index=True)
    product_id: Mapped[str] = mapped_column(String(128), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(128), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


Base.metadata.create_all(engine)

app = FastAPI(title="YOW Content & Commerce API", version="0.3.0")


@app.get("/v1/products")
def products():
    return {"products": [{"id": "yow-core", "name": "YOW Core", "version": "0.1.0", "platform": "android"}]}


WEB_DIR = Path(__file__).resolve().parents[1] / "web"
app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")


class DeviceBind(BaseModel):
    account_id: str = Field(min_length=3, max_length=128)
    device_id: str = Field(min_length=8, max_length=256)


class PaymentWebhook(BaseModel):
    provider: str
    provider_event_id: str = Field(min_length=3, max_length=256)
    account_id: str
    order_id: str
    product_id: str
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=16)
    status: Literal["paid", "failed", "refunded"]


def sign_token(account_id: str, product_id: str, device_id: str, expires_at: int) -> str:
    payload = f"{account_id}:{product_id}:{device_id}:{expires_at}"
    digest = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{expires_at}.{digest}"


@app.get("/health")
def health():
    return {"ok": True, "service": "yow-portal", "version": app.version}


@app.post("/v1/devices/bind")
def bind_device(req: DeviceBind, x_session_id: str | None = Header(default=None)):
    if not x_session_id:
        raise HTTPException(status_code=401, detail="جلسة مطلوبة")

    with Session(engine) as db:
        authenticated = get_session_account(db, AccessSession, x_session_id)
        if authenticated is None:
            raise HTTPException(status_code=401, detail="جلسة غير صالحة")
        if authenticated != req.account_id:
            raise HTTPException(status_code=403, detail="الحساب لا يطابق الجلسة")

        entitlement = db.scalar(
            select(Entitlement).where(
                Entitlement.account_id == req.account_id,
                Entitlement.active.is_(True),
            )
        )
        if entitlement is None:
            raise HTTPException(status_code=403, detail="active entitlement required")

        device = db.get(Device, req.device_id)
        if device is None:
            device = Device(id=req.device_id, account_id=req.account_id, active=True)
            db.add(device)
        elif device.account_id != req.account_id or not device.active:
            raise HTTPException(status_code=403, detail="device not available")
        db.commit()
    return {"account_id": req.account_id, "device_id": req.device_id, "status": "bound"}


@app.post("/v1/payments/webhook")
async def payment_webhook(
    request: Request,
    x_provider_signature: str | None = Header(default=None),
):
    secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
    raw_body = await request.body()
    if not secret:
        raise HTTPException(status_code=503, detail="payment webhook secret is not configured")
    try:
        payload = parse_signed_webhook(raw_body, x_provider_signature, secret)
        event = PaymentWebhook.model_validate(payload)
    except WebhookValidationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="invalid webhook payload") from exc

    with Session(engine) as db:
        if db.get(PaymentEvent, event.provider_event_id):
            return {"accepted": True, "idempotent": True}

        db.add(PaymentEvent(
            provider_event_id=event.provider_event_id,
            provider=event.provider,
            order_id=event.order_id,
            status=event.status,
        ))

        order = db.get(Order, event.order_id)
        if order is None:
            if event.status == "refunded":
                raise HTTPException(status_code=409, detail="refund requires an existing order")
            order = Order(
                id=event.order_id,
                account_id=event.account_id,
                product_id=event.product_id,
                amount_minor=event.amount_minor,
                currency=event.currency,
                status=event.status,
            )
            db.add(order)
        else:
            if (
                order.account_id != event.account_id
                or order.product_id != event.product_id
                or order.amount_minor != event.amount_minor
                or order.currency != event.currency
            ):
                raise HTTPException(status_code=409, detail="webhook does not match existing order")
            if order.status == "refunded" and event.status == "paid":
                raise HTTPException(status_code=409, detail="refunded order cannot be reopened by webhook")
            order.status = event.status

        existing = db.scalar(
            select(Entitlement).where(
                Entitlement.account_id == event.account_id,
                Entitlement.product_id == event.product_id,
            )
        )
        if event.status == "paid":
            if existing is None:
                db.add(Entitlement(
                    id=secrets.token_urlsafe(18),
                    account_id=event.account_id,
                    product_id=event.product_id,
                    active=True,
                ))
            else:
                existing.active = True
        elif event.status == "refunded" and existing:
            existing.active = False

        db.commit()

    return {"accepted": True, "entitlement_granted": event.status == "paid"}


@app.post("/v1/download-token")
def download_token(
    account_id: str,
    product_id: str,
    device_id: str,
    x_session_id: str | None = Header(default=None),
):
    if not x_session_id:
        raise HTTPException(status_code=401, detail="جلسة مطلوبة")

    with Session(engine) as db:
        authenticated = get_session_account(db, AccessSession, x_session_id)
        if authenticated is None:
            raise HTTPException(status_code=401, detail="جلسة غير صالحة")
        if authenticated != account_id:
            raise HTTPException(status_code=403, detail="الحساب لا يطابق الجلسة")

        entitlement = db.scalar(select(Entitlement).where(
            Entitlement.account_id == account_id,
            Entitlement.product_id == product_id,
            Entitlement.active.is_(True),
        ))
        device = db.get(Device, device_id)

    if entitlement is None:
        raise HTTPException(status_code=403, detail="active entitlement required")
    if device is None or device.account_id != account_id or not device.active:
        raise HTTPException(status_code=403, detail="bound device required")

    expires_at = int(time.time()) + TOKEN_TTL
    return {
        "token": sign_token(account_id, product_id, device_id, expires_at),
        "expires_in": TOKEN_TTL,
        "product_id": product_id,
    }


@app.get("/v1/download")
def download(
    account_id: str,
    product_id: str,
    device_id: str,
    x_download_token: str | None = Header(default=None),
    x_session_id: str | None = Header(default=None),
):
    if not x_session_id:
        raise HTTPException(status_code=401, detail="جلسة مطلوبة")
    if not x_download_token:
        raise HTTPException(status_code=401, detail="download token required")

    with Session(engine) as db:
        authenticated = get_session_account(db, AccessSession, x_session_id)
        if authenticated is None:
            raise HTTPException(status_code=401, detail="جلسة غير صالحة")
        if authenticated != account_id:
            raise HTTPException(status_code=403, detail="الحساب لا يطابق الجلسة")

        entitlement = db.scalar(select(Entitlement).where(
            Entitlement.account_id == account_id,
            Entitlement.product_id == product_id,
            Entitlement.active.is_(True),
        ))
        device = db.get(Device, device_id)

    registered = ARTIFACT_REGISTRY.get(product_id)
    artifact = (
        Artifact(product_id=registered.product_id, storage_url=registered.storage_url)
        if registered is not None and registered.storage_url
        else None
    )
    try:
        authorized = authorize_download(
            token=x_download_token,
            account_id=account_id,
            product_id=product_id,
            device_id=device_id,
            signing_secret=SECRET,
            entitlement_active=entitlement is not None,
            device_owner=device.account_id if device else None,
            device_active=device.active if device else False,
            artifact=artifact,
        )
    except DownloadServiceError as exc:
        if str(exc) == "paid artifact unavailable":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return {"product_id": authorized.product_id, "download_url": authorized.storage_url, "expires_in": TOKEN_TTL}


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)


@app.post("/v1/accounts/register")
def register_account(payload: RegisterRequest):
    try:
        email = normalize_email(payload.email)
    except ValueError:
        raise HTTPException(status_code=422, detail="بريد إلكتروني غير صالح")
    with Session(engine) as db:
        if db.scalar(select(Account).where(Account.email == email)):
            raise HTTPException(status_code=409, detail="الحساب موجود")
        account = Account(
            id=secrets.token_urlsafe(24),
            email=email,
            password_hash=hash_password(payload.password),
        )
        db.add(account)
        db.commit()
    return {"account_id": account.id, "email": account.email}


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)


@app.post("/v1/accounts/login")
def login(payload: LoginRequest):
    try:
        email = normalize_email(payload.email)
    except ValueError:
        raise HTTPException(status_code=422, detail="بريد إلكتروني غير صالح")
    with Session(engine) as db:
        account = db.scalar(select(Account).where(Account.email == email))
        if account is None or not verify_password(payload.password, account.password_hash):
            raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
        session_id = secrets.token_urlsafe(32)
        db.add(AccessSession(id=session_id, account_id=account.id, active=True))
        db.commit()
    return {"session_id": session_id, "account_id": account.id}


@app.get("/v1/accounts/{account_id}")
def account_profile(account_id: str, x_session_id: str | None = Header(default=None)):
    if not x_session_id:
        raise HTTPException(status_code=401, detail="جلسة مطلوبة")
    with Session(engine) as db:
        authenticated = get_session_account(db, AccessSession, x_session_id)
        if authenticated is None:
            raise HTTPException(status_code=401, detail="جلسة غير صالحة")
        if authenticated != account_id:
            raise HTTPException(status_code=403, detail="الحساب لا يطابق الجلسة")
        account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    return {"account_id": account.id, "email": account.email}


@app.post("/v1/accounts/session/revoke")
def revoke_session(session_id: str, x_session_id: str | None = Header(default=None)):
    if not x_session_id:
        raise HTTPException(status_code=401, detail="جلسة مطلوبة")
    with Session(engine) as db:
        authenticated = get_session_account(db, AccessSession, x_session_id)
        target = db.get(AccessSession, session_id)
        if authenticated is None:
            raise HTTPException(status_code=401, detail="جلسة غير صالحة")
        if target is None:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        if target.account_id != authenticated:
            raise HTTPException(status_code=403, detail="لا يمكن إلغاء جلسة حساب آخر")
        target.active = False
        db.commit()
    return {"revoked": True}
