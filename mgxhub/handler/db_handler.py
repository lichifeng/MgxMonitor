'''Used to communicate with the database.
This version is for SQLite only. Need modification for other databases.
'''

# pylint: disable=E1102

import os
from datetime import datetime
from hashlib import md5

from sqlalchemy import asc, create_engine, desc, func, text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from mgxhub.config import cfg
from mgxhub.logger import logger
from mgxhub.model.orm import Base, Chat, File, Game, LegacyInfo, Player
from mgxhub.model.searchcriteria import SearchCriteria
from mgxhub.model.webapi import GameDetail

from ..util import sanitize_playername


class DBHandler:
    '''Communicate with the database.'''

    _db_path = None
    _db_engine = None
    _db_session = None

    def __init__(self, db_path: str | None = None):
        '''Initialize the database handler.

        Args:
            db_path: Path to the database file. If an relative path is given, it will be joined with the project root.
        '''

        if db_path is None:
            self._db_path = cfg.get('database', 'sqlite')
        else:
            self._db_path = db_path
        self._load_db(self._db_path)

    def _load_db(self, db_path: str) -> None:
        '''Load the database.

        Args:
            db_path: Path to the database file.
        '''

        db_path = os.path.join(cfg.get('system', 'projectroot'), db_path)
        self._db_engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._db_engine)
        self._db_session = Session(self._db_engine)
        logger.debug(f"Database loaded: {db_path}")  # Watcher thread will print this, too.

    def __del__(self):
        if self._db_session:
            self._db_session.close()
        if self._db_engine:
            self._db_engine.dispose()

    @property
    def session(self) -> Session:
        '''Get the database session.'''

        return self._db_session

    def get_record_files(self, game_guid: str) -> list[str]:
        '''Get record files(md5) of a game by its GUID.

        Args:
            game_guid: GUID of the game.
        '''

        files = self.session.query(File.md5).filter(File.game_guid == game_guid).all()
        return [f[0] for f in files]

    def set_visibility(self, game_guid: str, level: int = 0) -> bool:
        '''Set visibility level of a game.

        Args:
            game_guid: GUID of the game.
            level: Visibility level. 0 for public, 1 for private, 2 for unlisted.
        '''

        game = self.session.query(Game).filter(
            Game.game_guid == game_guid).first()
        if game:
            game.visibility = level
            self.session.commit()
            return True
        return False

    def delete_game(self, game_guid: str) -> bool:
        '''Delete a game by its GUID.

        Args:
            game_guid: GUID of the game.
        '''

        game = self.session.query(Game).filter(Game.game_guid == game_guid).first()
        if game:
            self.session.query(Player).filter(
                Player.game_guid == game_guid).delete()
            self.session.query(Chat).filter(
                Chat.game_guid == game_guid).delete()
            self.session.query(File).filter(
                File.game_guid == game_guid).delete()
            self.session.query(LegacyInfo).filter(
                LegacyInfo.game_guid == game_guid).delete()
            self.session.delete(game)
            self.session.commit()
            logger.info(f"[DB] Delete: {game_guid}")
            return True
        return False

    def fetch_rating_meta(self) -> dict:
        '''Get rating meta data.'''

        query = text("""
            SELECT version_code, COUNT(*) as count
            FROM ratings
            GROUP BY version_code
            ORDER BY count DESC;
        """)

        result = self.session.execute(query)
        meta = [tuple(row) for row in result.fetchall()]
        current_time = datetime.now().isoformat()
        return {'meta': meta, 'generated_at': current_time}

    async def async_fetch_rating_meta(self) -> dict:
        '''Async version of fetch_rating_meta()'''

        return self.fetch_rating_meta()

    def fetch_rating(
        self,
        version_code: str = 'AOC10',
        matchup: str = '1v1',
        order: str = 'desc',
        page: int = 0,
        page_size: int = 100,
    ) -> dict:
        '''Get ratings information.

        Args:
            version_code: Version code of the game.
            matchup: Matchup of the game.
            page_size: page size of the result.
        '''

        matchup_value = '1v1' if matchup.lower() == '1v1' else 'team'
        order_method = 'DESC' if order.lower() == 'desc' else 'ASC'
        if page < 0 or page_size < 1:
            return {'ratings': [], 'generated_at': datetime.now().isoformat()}

        sql = text(f"""
            SELECT ROW_NUMBER() OVER (ORDER BY rating {order_method}) AS rownum,
                name,
                name_hash,
                rating,
                total,
                wins,
                streak,
                streak_max,
                highest,
                lowest,
                first_played,
                last_played
            FROM ratings
            WHERE version_code = :version_code AND matchup = :matchup_value
            ORDER BY rating {order_method}
            LIMIT :page_size
            OFFSET :page;
        """)

        ratings = self.session.execute(
            sql,
            {
                "version_code": version_code,
                "matchup_value": matchup_value,
                "page_size": page_size,
                "page": page * page_size
            }
        ).fetchall()
        ratings = [list(row) for row in ratings]
        current_time = datetime.now().isoformat()
        return {'ratings': ratings, 'generated_at': current_time}

    def fetch_player_rating(
        self,
        name_hash: str,
        version_code: str = 'AOC10',
        matchup: str = '1v1',
        order: str = 'desc',
        page_size: int = 100,
    ) -> dict:
        '''Get ratings information of a player.

        Args:
            name_hash: the name_hash of the player.
            version_code: Version code of the game.
            matchup: Matchup of the game.
            page_size: page size.
        '''

        matchup_value = '1v1' if matchup.lower() == '1v1' else 'team'
        order_method = 'DESC' if order.lower() == 'desc' else 'ASC'
        if page_size < 1:
            return {'ratings': [], 'generated_at': datetime.now().isoformat()}

        sql = text(f"""
            WITH rating_table AS (
                SELECT ROW_NUMBER() OVER (ORDER BY rating {order_method}) AS rownum,
                    name,
                    name_hash,
                    rating,
                    total,
                    wins,
                    streak,
                    streak_max,
                    highest,
                    lowest,
                    first_played,
                    last_played
                FROM ratings
                WHERE version_code = :version_code AND matchup = :matchup_value
                ORDER BY rating {order_method}
            ), name_hash_index AS (
                SELECT rownum FROM rating_table WHERE name_hash = :name_hash
            )
            SELECT * FROM rating_table
            WHERE rownum > (SELECT rownum FROM name_hash_index) / :page_size * :page_size AND rownum <= ((SELECT rownum FROM name_hash_index) / :page_size + 1) * :page_size
            ORDER BY rownum
            LIMIT :page_size;
        """)

        ratings = self.session.execute(
            sql,
            {
                "version_code": version_code,
                "matchup_value": matchup_value,
                "page_size": page_size,
                "name_hash": name_hash.lower() if name_hash else None
            }
        ).fetchall()
        ratings = [list(row) for row in ratings]
        current_time = datetime.now().isoformat()
        return {'ratings': ratings, 'generated_at': current_time}
