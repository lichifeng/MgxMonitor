from sqlalchemy.orm import Session

from .sqlite3 import SQLite3Factory


def db() -> Session:
    '''Provide a SQLite3 session.'''

    return SQLite3Factory()()()
