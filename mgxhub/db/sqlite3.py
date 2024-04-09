'''Establish a SQLite3 connection and provide a SQLAlchemy session.'''

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mgxhub import cfg, logger
from mgxhub.model.orm import Base
from mgxhub.singleton import Singleton


class SQLite3:
    '''Provide a SQLAlchemy session.'''

    def __init__(self, session: Session):
        self.session = session

    def __call__(self) -> Session:
        return self.session

    def __del__(self):
        self.session.close()


class SQLite3Factory(metaclass=Singleton):
    '''Establish a SQLite3 connection and provide a SQLAlchemy session.'''

    _db_path = None
    _db_engine = None
    _db_sessionlocal = None

    def __init__(self, db_path: str | None = None):
        '''Initialize the database handler.

        Only one instance of Database is allowed, use `load()` to change the
        database file.

        Args:
            db_path: Path to the database file. If an relative path is given, it
            will be joined with the project root.
        '''

        self.prepare(db_path)

    def __del__(self):
        if self._db_engine:
            self._db_engine.dispose()

    def __call__(self, db_path: str | None = None) -> SQLite3:
        if db_path is not None:
            self.prepare(db_path)
        return SQLite3(self._db_sessionlocal())

    def prepare(self, db_path: str | None = None) -> None:
        '''Prepare a database engine.

        Args:
            db_path: Path to the database file.
        '''

        if db_path is None:
            db_path = cfg.get('database', 'sqlite')
        self._db_path = os.path.join(cfg.get('system', 'projectroot'), db_path)

        self._db_engine = create_engine(
            f"sqlite:///{self._db_path}",
            connect_args={"check_same_thread": False},
            echo=(cfg.get('system', 'echosql').lower() == 'on')
        )
        Base.metadata.create_all(self._db_engine)
        self._db_sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=self._db_engine)
        logger.debug(f"SQLite prepared: {self._db_path}")
