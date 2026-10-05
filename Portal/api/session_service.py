"""Session-domain helpers kept independent from HTTP route wiring."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session


def create_session(db: Session, session_model, account_id: str, session_id: str) -> object:
    row = session_model(id=session_id, account_id=account_id, active=True)
    db.add(row)
    db.commit()
    return row


def revoke_session(db: Session, session_model, session_id: str) -> bool:
    row = db.scalar(select(session_model).where(session_model.id == session_id))
    if row is None or not row.active:
        return False
    row.active = False
    db.commit()
    return True


def get_session_account(db: Session, session_model, session_id: str) -> str | None:
    row = db.scalar(
        select(session_model).where(
            session_model.id == session_id,
            session_model.active.is_(True),
        )
    )
    return row.account_id if row is not None else None
