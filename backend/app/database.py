from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = dict(
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)
if not _is_sqlite:
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

if _is_sqlite:
    # Enable foreign-key enforcement in SQLite
    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
_sqlite_migrated = False


def get_db() -> Generator[Session, None, None]:
    global _sqlite_migrated
    if _is_sqlite and not _sqlite_migrated:
        _ensure_columns()
        _sqlite_migrated = True
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_columns() -> None:
    """Add columns introduced after the first SQLite database was created."""
    if not _is_sqlite:
        return
    statements = {
        "users": {
            "email_verification_token": "VARCHAR(128)",
            "email_verification_expires": "DATETIME",
            "password_reset_token": "VARCHAR(128)",
            "password_reset_expires": "DATETIME",
            "refresh_token_hash": "VARCHAR(128)",
            "jurisdiction_boundary_id": "INTEGER",
        },
        "issues": {
            "ai_status": "VARCHAR(40)",
        },
    }
    with engine.begin() as conn:
        for table, columns in statements.items():
            existing = {
                row[1]
                for row in conn.execute(text(f"PRAGMA table_info({table})"))
            }
            if not existing:
                continue
            for name, ddl in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def init_db() -> None:
    """Create all tables. Call once at startup in development."""
    from app.models import activity, civic, evidence, gps_photo, issue, location, resolution, saved_place, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_columns()
