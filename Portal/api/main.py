from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import hashlib
import hmac
import os
import secrets

app = FastAPI(title="YOW Content & Commerce API", version="0.1.0")

SECRET = os.getenv("ENTITLEMENT_SIGNING_SECRET", "CHANGE_ME_IN_PRODUCTION").encode()

class DeviceBind(BaseModel):
    account_id: str = Field(min_length=3, max_length=128)
    device_id: str = Field(min_length=8, max_length=256)

class PaymentWebhook(BaseModel):
    provider: str
    provider_event_id: str
    account_id: str
    order_id: str
    amount_minor: int
    currency: str
    status: Literal["paid", "failed", "refunded"]

def sign_entitlement(account_id: str, product_id: str, device_id: str) -> str:
    payload = f"{account_id}:{product_id}:{device_id}"
    return hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()

@app.get("/health")
def health():
    return {"ok": True, "service": "yow-portal"}

@app.post("/v1/devices/bind")
def bind_device(req: DeviceBind):
    # Production: read an existing paid entitlement from PostgreSQL.
    # Do not grant access merely because this endpoint was called.
    return {"account_id": req.account_id, "device_id": req.device_id, "status": "pending_entitlement"}

@app.post("/v1/payments/webhook")
def payment_webhook(event: PaymentWebhook):
    # Production: verify provider signature before accepting this request.
    # The webhook must be idempotent on provider_event_id.
    if event.status != "paid":
        return {"accepted": True, "entitlement_granted": False}
    return {"accepted": True, "entitlement_granted": True, "order_id": event.order_id}

@app.post("/v1/download-token")
def download_token(account_id: str, product_id: str, device_id: str):
    # Production: query entitlement(account_id, product_id), device status,
    # refund state, release state and rate limits before issuing a token.
    token = sign_entitlement(account_id, product_id, device_id)
    return {"token": token, "expires_in": 900, "product_id": product_id}
