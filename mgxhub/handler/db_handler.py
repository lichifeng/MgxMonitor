'''Used to communicate with the database.
This version is for SQLite only. Need modification for other databases.
'''

import os
from datetime import datetime
from hashlib import md5
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from mgxhub.model.orm import Base, Game, Player, File, Chat, Rating, LegacyInfo
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

    def add_game(self, d: dict, t: str | None = None, source: str = "") -> tuple[str, str]:
        '''Add a game to the database.

        Args:
            d: Game data from the parser.
            t: Time of the game played. Normall last modified time of the actually record file in ISO format.
            source: Source of the record file. User uploaded from web, or from the bot, etc.

        Returns:
            A tuple of two strings. The first string is the status of the operation, which is one of "exists", "invalid", "success". The second string is the GUID of the game. 
        '''
        game = self.session.query(Game).filter(
            Game.game_guid == d.get('guid')).first()
        if game:
            if isinstance(game.duration, (int, float)) and game.duration > d.get('duration'):
                return "exists", game.game_guid

        if not d.get('guid'):
            return "invalid", "missing guid"

        # game_time is deduced from file creation time which is not trustable.
        # Earlier time **NORMALLY** means better chance not modified. And date
        # earlier than publication of Age of Empires II is invalid. Anyway, this
        # value is not trustable.
        game_time = datetime.fromtimestamp(
            d.get('gameTime')) if d.get('gameTime') else datetime.now()
        if t:
            try:
                t_input = datetime.fromisoformat(t)
                game_time = min(game_time, t_input)
            except ValueError:
                pass
        if game_time < datetime(1999, 3, 30):
            game_time = datetime.now()

        merged_game = self.session.merge(Game(
            id=game.id if game else None,
            game_guid=d.get('guid'),
            duration=d.get('duration'),
            include_ai=d.get('includeAI'),
            is_multiplayer=d.get('isMultiplayer'),
            population=d.get('population'),
            speed=d.get('speedEn'),
            matchup=d.get('matchup'),
            map_name=d.get('map', {}).get('nameEn'),
            map_size=d.get('map', {}).get('sizeEn'),
            version_code=d.get('version', {}).get('code'),
            version_log=d.get('version', {}).get('logVer'),
            version_raw=d.get('version', {}).get('rawStr'),
            version_save=d.get('version', {}).get('saveVer'),
            version_scenario=d.get('version', {}).get('scenarioVersion'),
            victory_type=d.get('victory', {}).get('typeEn'),
            instruction=d.get('instruction'),
            game_time=game_time
        ))

        player_batch = []
        players = d.get('players')
        if players:
            # delete old records where game_guid = d.get('guid')
            self.session.query(Player).filter(
                Player.game_guid == d.get('guid')).delete()

            for p in players:
                player_batch.append({
                    'game_guid': d.get('guid'),
                    'slot': p.get('slot'),
                    'index_player': p.get('index'),
                    'name': p.get('name'),
                    'name_hash': md5(p.get('name').encode("utf-8")).hexdigest() if p.get('name') else None,
                    'type': p.get('typeEn'),
                    'team': p.get('team'),
                    'color_index': p.get('colorIndex'),
                    'init_x': p.get('initPosition', [-1, -1])[0],
                    'init_y': p.get('initPosition', [-1, -1])[1],
                    'disconnected': p.get('disconnected'),
                    'is_winner': p.get('isWinner'),
                    'is_main_operator': p.get('mainOp'),
                    'civ_id': p.get('civilization', {}).get('id'),
                    'civ_name': p.get('civilization', {}).get('nameEn'),
                    'feudal_time': p.get('feudalTime'),
                    'castle_time': p.get('castleTime'),
                    'imperial_time': p.get('imperialTime'),
                    'resigned_time': p.get('resigned')
                })
            self.session.bulk_insert_mappings(Player, player_batch)

        record_file = File(
            game_guid=d.get('guid'),
            md5=d.get('md5'),
            parser=d.get('parser'),
            parse_time=d.get('parseTime'),
            parsed_status=d.get('status'),
            raw_filename=d.get('realfile'),
            raw_lastmodified=game_time,
            notes=d.get('message'),
            recorder_slot=d.get('recPlayer'),
            source=source
        )
        self.session.add(record_file)

        chats = d.get('chat')
        if chats:
            for c in chats:
                chat = {
                    'game_guid': d.get('guid'),
                    'chat_time': c.get('time'),
                    'chat_content': c.get('msg')
                }
                stmt = insert(Chat).values(chat).on_conflict_do_nothing(
                    index_elements=['game_guid', 'chat_time', 'chat_content'])
                self.session.execute(stmt)

        self.session.commit()

        if game:
            return "updated", merged_game.game_guid
        return "success", merged_game.game_guid

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
        game = self.session.query(Game).filter(
            Game.game_guid == game_guid).first()
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
            return True
        return False

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
