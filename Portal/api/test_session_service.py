from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    __tablename__ = "access_sessions"
    id: Mapped[str] = mapped_column(primary_key=True)
    account_id: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_create_and_resolve_active_session():
    from session_service import create_session, get_session_account

    engine = make_db()
    with Session(engine) as db:
        create_session(db, SessionRow, "acct-123456", "sess-123456")
        assert get_session_account(db, SessionRow, "sess-123456") == "acct-123456"


def test_revoke_invalidates_session():
    from session_service import create_session, get_session_account, revoke_session

    engine = make_db()
    with Session(engine) as db:
        create_session(db, SessionRow, "acct-123456", "sess-123456")
        assert revoke_session(db, SessionRow, "sess-123456") is True
        assert get_session_account(db, SessionRow, "sess-123456") is None
        assert revoke_session(db, SessionRow, "sess-123456") is False


def test_unknown_session_is_not_authenticated():
    from session_service import get_session_account

    engine = make_db()
    with Session(engine) as db:
        assert get_session_account(db, SessionRow, "missing-session") is None
