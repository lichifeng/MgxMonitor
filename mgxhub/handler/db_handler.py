'''Used to communicate with the database.
This version is for SQLite only. Need modification for other databases.
'''

import os
from datetime import datetime
from hashlib import md5
from sqlalchemy import create_engine, asc, text, desc, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from mgxhub.model.orm import Base, Game, Player, File, Chat, LegacyInfo, Rating
from mgxhub.model.webapi import GameDetail
from mgxhub.config import cfg
from mgxhub.logger import logger


class DBHandler:
    '''Communicate with the database.'''

    _db_path = None
    _db_engine = None
    _db_session = None

    def __init__(self, db_path: str | None = None):
        '''Initialize the database handler.

        Args:
            db_path: Path to the database file. 
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
        logger.debug(f"Database loaded: {db_path}") # Watcher thread will print this, too.


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

        game = self.session.query(Game).filter(Game.game_guid == d.get('guid')).first()
        if game and isinstance(game.duration, (int, float)):
            if game.duration > d.get('duration'):
                return "exists", game.game_guid
            if game.duration == d.get('duration'):
                same_file = self.session.query(File).filter(File.md5 == d.get('md5')).first()
                if same_file:
                    return "duplicated", game.game_guid

        if not d.get('guid'):
            return "invalid", "missing guid"

        # game_time is deduced from file creation time which is not trustable.
        # Earlier time **NORMALLY** means better chance not modified. And date
        # earlier than publication of Age of Empires II is invalid. Anyway, this
        # value is not trustable.
        game_time = datetime.fromtimestamp(d.get('gameTime')) if d.get('gameTime') else datetime.now()
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
            self.session.query(Player).filter(Player.game_guid == d.get('guid')).delete()

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
                stmt = insert(Chat).values(chat).on_conflict_do_nothing(index_elements=['game_guid', 'chat_time', 'chat_content'])
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


    def fetch_index_stats(self) -> dict:
        '''Unique games/players count, new games this month.'''

        query = text("""
            SELECT 'unique_games', COUNT(DISTINCT game_guid) AS count FROM games
            UNION ALL
            SELECT 'unique_players', COUNT(DISTINCT name_hash) FROM players
            UNION ALL
            SELECT 'monthly_games', COUNT(*) FROM games WHERE strftime('%m', modified) = strftime('%m', datetime('now', '-1 month')) AND strftime('%Y', modified) = strftime('%Y', 'now')
        """)

        result = self.session.execute(query)
        results = result.fetchall()
        stats = {name: count for name, count in results}

        # Add the current time to the stats
        stats['generated_at'] = datetime.now().isoformat()

        return stats


    def fetch_rand_players(self, threshold: int = 10, limit: int = 300) -> dict:
        '''Random players.

        Including total games of each player. Used mainly in player cloud.

        Args:
            threshold: minimum games of a player to be included.
            limit: maximum number of players to be included. Max is 1000.
        '''

        if not isinstance(threshold, int) or threshold <= 0:
            threshold = 10
        if not isinstance(limit, int) or limit <= 0 or limit > 1000:
            limit = 300

        query = text("""
            SELECT name, game_count FROM (
                SELECT name, COUNT(game_guid) as game_count
                FROM players
                GROUP BY name
                HAVING game_count > :threshold
            ) AS player_counts
            ORDER BY RANDOM()
            LIMIT :limit
        """)

        result = self.session.execute(query, {'threshold': threshold, 'limit': limit})
        players = [{'name': row.name, 'name_hash': md5(str(row.name).encode('utf-8')).hexdigest(), 'game_count': row.game_count} for row in result]
        current_time = datetime.now().isoformat()
        return {'players': players, 'generated_at': current_time}


    def fetch_latest_players(self, limit: int = 300) -> dict:
        '''Newly found players.

        Including won games, total games, and 1v1 games counts.

        Args:
            limit: maximum number of players to be included.
        '''

        query = text("""
            SELECT 
                ep.name, 
                ep.latest_created, 
                (SELECT COUNT(*) FROM players WHERE name = ep.name AND is_winner = 1) AS win_count,
                (SELECT COUNT(*) FROM players WHERE name = ep.name) AS total_games,
                (SELECT COUNT(*) FROM games g JOIN players p ON g.game_guid = p.game_guid WHERE p.name = ep.name AND g.matchup = '1v1') AS total_1v1_games
            FROM 
                (SELECT 
                    name,
                    MAX(created) AS latest_created
                FROM 
                    players
                GROUP BY 
                    name
                LIMIT :limit) AS ep
            ORDER BY 
                ep.latest_created DESC;
        """)

        result = self.session.execute(query, {'limit': limit})
        players = [list(row) for row in result.fetchall()]
        current_time = datetime.now().isoformat()
        return {'players': players, 'generated_at': current_time}


    def fetch_close_friends(self, name_hash: str, limit: int = 100) -> list:
        '''Players who played with the given player most.

        Args:
            name_hash: the name_hash of the player.
            limit: maximum number of players to be included.
        '''

        query = text("""
            SELECT 
                p2.name, 
                COUNT(*) AS common_games_count
            FROM 
                players p1
            JOIN 
                players p2 ON p1.game_guid = p2.game_guid
            WHERE 
                p1.name_hash = :name_hash AND p1.name != p2.name
            GROUP BY 
                p2.name
            ORDER BY 
                common_games_count DESC
            LIMIT :limit;
        """)

        result = self.session.execute(query, {'name_hash': name_hash, 'limit': limit})
        players = [list(row) for row in result.fetchall()]
        current_time = datetime.now().isoformat()
        return {'players': players, 'generated_at': current_time}


    def fetch_latest_games(self, limit: int = 20) -> dict:
        '''Get recently uploaded games.

        Args:
            limit: maximum number of games to be included.
        '''

        query = text("""
            WITH latest_games AS (
                SELECT 
                    g.game_guid, g.version_code, g.created, g.map_name, g.matchup, g.duration, g.speed, f.recorder_slot
                FROM 
                    (SELECT * FROM games ORDER BY created DESC LIMIT :limit) AS g
                JOIN 
                    files AS f ON g.game_guid = f.game_guid
                WHERE 
                    f.created = (SELECT MIN(created) FROM files WHERE game_guid = g.game_guid)
            )
            SELECT latest_games.*, p.name 
            FROM latest_games
            JOIN players AS p ON latest_games.game_guid = p.game_guid AND latest_games.recorder_slot = p.slot;
        """)

        result = self.session.execute(query, {'limit': limit})
        games = [list(row) for row in result.fetchall()]
        current_time = datetime.now().isoformat()
        return {'games': games, 'generated_at': current_time}


    def fetch_rand_games(self, threshold: int = 10, limit: int = 50) -> dict:
        '''Get random games.

        Args:
            threshold: minimum duration in minutes.
            limit: maximum number of games to be included.
        '''

        query = text("""
            SELECT 
                game_guid, version_code, created, map_name, matchup, duration, speed 
            FROM games 
            WHERE duration > :threshold 
            ORDER BY RANDOM()
            LIMIT :limit;
        """)

        result = self.session.execute(query, {'threshold': threshold * 60, 'limit': limit})
        games = [list(row) for row in result.fetchall()]
        current_time = datetime.now().isoformat()
        return {'games': games, 'generated_at': current_time}


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
            offset: int = 0,
            limit: int = 100
    ) -> dict:
        '''Get ratings information.

        Args:
            version_code: Version code of the game.
            matchup: Matchup of the game.
            limit: maximum number of players to be included.
        '''

        matchup_value = '1v1' if matchup.lower() == '1v1' else 'team'
        order_method = desc if order.lower() == 'desc' else asc

        ratings = self.session.query(
                        Rating.name,
                        Rating.name_hash, 
                        Rating.rating,
                        Rating.total,
                        Rating.wins,
                        Rating.streak,
                        Rating.streak_max,
                        Rating.highest,
                        Rating.lowest,
                        Rating.first_played,
                        Rating.last_played
                    )\
                    .filter(
                        Rating.version_code == version_code, 
                        Rating.matchup == matchup_value
                    )\
                    .order_by(order_method(Rating.rating))\
                    .limit(limit)\
                    .offset(offset)\
                    .all()

        ratings = [list(row) for row in ratings]
        current_time = datetime.now().isoformat()
        return {'ratings': ratings, 'generated_at': current_time}
