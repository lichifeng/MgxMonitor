'''Establish a SQLite3 connection and provide a SQLAlchemy session.'''

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mgxhub import cfg, logger
from mgxhub.model.orm import Base
from mgxhub.singleton import Singleton


class SQLite3(metaclass=Singleton):
    '''Establish a SQLite3 connection and provide a SQLAlchemy session.'''

    _db_path = None
    _db_engine = None
    _db_session = None

    def __init__(self, db_path: str | None = None):
        '''Initialize the database handler.

        Only one instance of Database is allowed, use `load()` to change the
        database file.

        Args:
            db_path: Path to the database file. If an relative path is given, it
            will be joined with the project root.
        '''

        self.load(db_path)

    def __del__(self):
        if self._db_session:
            self._db_session.close()
        if self._db_engine:
            self._db_engine.dispose()

    def __call__(self, db_path: str | None = None) -> Session:
        if db_path is not None:
            self.load(db_path)
        return self._db_session

    def load(self, db_path: str | None = None) -> None:
        '''Load a database.

        Args:
            db_path: Path to the database file.
        '''

        if db_path is None:
            db_path = cfg.get('database', 'sqlite')
        self._db_path = os.path.join(cfg.get('system', 'projectroot'), db_path)

        self._db_engine = create_engine(f"sqlite:///{self._db_path}",
                                        echo=(cfg.get('system', 'loglevel').upper() == 'DEBUG'))
        Base.metadata.create_all(self._db_engine)
        self._db_session = Session(self._db_engine)
        logger.debug(f"SQLite loaded: {self._db_path}")  # Watcher thread will print this, too.
