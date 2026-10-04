from collections.abc import Generator
from sqlalchemy.orm import Session
from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for a FastAPI request.
    The session is automatically closed after the request,
    whether the request succeeds or fails.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()