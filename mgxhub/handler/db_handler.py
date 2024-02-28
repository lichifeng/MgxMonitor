'''Used to communicate with the database.
This version is for SQLite only. Need modification for other databases.
'''

import os
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import Session
from mgxhub.model.orm import Base, Game, Player, File, Chat, Rating
from mgxhub.model.webapi import GameDetail


class DBHandler:
    '''Communicate with the database.'''

    _db_path = None
    _db_engine = None
    _db_session = None

    def __init__(self, db_path: str | None = None):
        '''Initialize the database handler.

        Args:
            db_path: Path to the database file. If not provided, it will use the
            value of environment variable `SQLITE_PATH` or `test_db.sqlite3`.
        '''
        if db_path is None:
            self._db_path = os.getenv('SQLITE_PATH', "test_db.sqlite3")
        else:
            self._db_path = db_path
        self._load_db(self._db_path)

    def _load_db(self, db_path: str) -> None:
        '''Load the database.

        Args:
            db_path: Path to the database file.
        '''
        self._db_engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._db_engine)
        self._db_session = Session(self._db_engine)

    def __del__(self):
        if self._db_session:
            self._db_session.close()
        if self._db_engine:
            self._db_engine.dispose()

    @property
    def session(self) -> Session:
        '''Get the database session.'''
        return self._db_session

    def get_game(self, game_guid: str, lang: str = 'en') -> GameDetail | None:
        '''Get details for a game by its GUID.

        Args:
            game_guid: GUID of the game.
            lang: Language code. Default is 'en'. Available translation files are under `translations/LC_MESSAGES/`.
        '''

        game_basic = self.session.query(Game).filter(
            Game.game_guid == game_guid).first()
        if game_basic is None:
            return None

        player_data = self.session.query(Player).filter(
            Player.game_guid == game_guid).all()
        file_data = self.session.query(File).filter(
            File.game_guid == game_guid).all()
        chat_data = self.session.query(Chat.chat_time, Chat.chat_content)\
            .filter(Chat.game_guid == game_guid)\
            .group_by(Chat.chat_time, Chat.chat_content)\
            .order_by(asc(Chat.chat_time))\
            .all()

        return GameDetail(game_basic, player_data, file_data, chat_data, lang)

    def add_game(self, game: dict) -> str:
        pass

    def delete_game(self, game_guid: str) -> bool:
        pass

    def stat_index_count(self) -> dict:
        '''Unique games/players count, new games this month.'''
        pass

    def stat_rand_players(self, threshold: int = 10, limit: int = 300) -> list:
        '''Random players.

        Including total games of each player. Used mainly in player cloud.

        Args:
            threshold: minimum games of a player to be included.
            limit: maximum number of players to be included.
        '''
        pass

    def stat_last_players(self, limit: int = 300) -> list:
        '''Newly found players.

        Including won games, total games, and 1v1 games counts.

        Args:
            limit: maximum number of players to be included.
        '''
        pass

    def stat_close_friends(self, player_name: str, limit: int = 300) -> list:
        '''Players who played with the given player most.'''
        pass

    def filter_games(self, filters: dict, limit: int = 100) -> list:
        '''Filter games by given conditions.'''
        pass

    def update_ratings(self, ratings_dict: dict, batch_size: int = None) -> bool:
        '''Update ratings of players.'''

        if batch_size is None:
            batch_size = len(ratings_dict)

        for i in range(0, len(ratings_dict), batch_size):
            self.session.bulk_insert_mappings(
                Rating, ratings_dict[i:i+batch_size])
            self.session.commit()
