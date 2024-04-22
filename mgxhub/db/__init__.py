from sqlalchemy.orm import Session

from .sqlite3 import SQLite3Factory


def db_raw() -> Session:
    '''Provide a SQLite3 session.'''

    return SQLite3Factory()()


def db_dep():
    '''Provide a SQLite3 session for FastAPI dependency injection.'''

    db = SQLite3Factory()()
    try:
        yield db
    finally:
        db.close()
