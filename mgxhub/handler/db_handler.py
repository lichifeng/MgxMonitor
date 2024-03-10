'''Used to communicate with the database.
This version is for SQLite only. Need modification for other databases.
'''

# pylint: disable=E1102

import os
import string
from datetime import datetime
from hashlib import md5
from sqlalchemy import create_engine, asc, desc, text, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from mgxhub.model.orm import Base, Game, Player, File, Chat, LegacyInfo
from mgxhub.model.webapi import GameDetail
from mgxhub.config import cfg
from mgxhub.logger import logger
from mgxhub.model.searchcriteria import SearchCriteria


def remove_unprintable_chars(s: str) -> str:
    '''Remove unprintable ASCII characters and whitespace from players' names.'''

    return ''.join(c for c in s if c in string.printable or ord(c) >= 0x80).strip()


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

    def _update_gametime(self, game: Game, game_time: datetime) -> bool:
        '''Update the game time of a game.

        Args:
            game_guid: GUID of the game.
            game_time: New game time.
        '''

        if game:
            game.game_time = game_time
            self.session.commit()
            logger.info(f'[DB] game_time updated: {game.game_guid}')
            return True
        return False

    def add_game(self, d: dict, t: str | None = None, source: str = "") -> tuple[str, str]:
        '''Add a game to the database.

        Args:
            d: Game data from the parser.
            t: Time of the game played. Normall last modified time of the actually record file in ISO format.
            source: Source of the record file. User uploaded from web, or from the bot, etc.

        Returns:
            A tuple of two strings. The first string is the status of the operation, which is one of "exists", "invalid", "success". The second string is the GUID of the game. 
        '''

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
        if game_time < datetime(1999, 3, 30) or game_time > datetime.now():
            game_time = datetime.now()

        game = self.session.query(Game).filter(Game.game_guid == d.get('guid')).first()
        if game and isinstance(game.duration, (int, float)):
            update_gametime = False
            if hasattr(game, 'game_time') and game_time < game.game_time:
                game.game_time = game_time
                update_gametime = True

            if game.duration > d.get('duration'):
                if update_gametime:
                    self._update_gametime(game, game_time)
                return "exists", game.game_guid
            if game.duration == d.get('duration'):
                same_file = self.session.query(File).filter(File.md5 == d.get('md5')).first()
                if same_file:
                    if update_gametime:
                        self._update_gametime(game, game_time)
                    return "duplicated", game.game_guid

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
                if p.get('name'):
                    sanitized_name = remove_unprintable_chars(p.get('name')) or '<NULL>'
                else:
                    sanitized_name = '<NULL>'

                player_batch.append({
                    'game_guid': d.get('guid'),
                    'slot': p.get('slot'),
                    'index_player': p.get('index'),
                    'name': sanitized_name,
                    'name_hash': md5(sanitized_name.encode('utf-8')).hexdigest(),
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
        players = [{'name': row.name, 'name_hash': md5(str(row.name).encode(
            'utf-8')).hexdigest(), 'game_count': row.game_count} for row in result]
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

    async def async_fetch_close_friends(self, name_hash: str, limit: int = 100) -> list:
        '''Async version of fetch_close_friends()'''

        return self.fetch_close_friends(name_hash, limit)

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

    def fetch_player_totals(self, name_hash: str) -> dict:
        '''Get profile of a player.

        Args:
            name_hash: the name_hash of the player.
        '''

        total_games = self.session.query(func.count(Game.game_guid.distinct()))\
            .join(Player, Game.game_guid == Player.game_guid).filter(Player.name_hash == name_hash).scalar()
        total_wins = self.session.query(func.count(Game.game_guid.distinct()))\
            .join(Player, Game.game_guid == Player.game_guid).filter(Player.name_hash == name_hash, Player.is_winner).scalar()
        total_1v1 = self.session.query(func.count(Game.game_guid.distinct()))\
            .join(Player, Game.game_guid == Player.game_guid).filter(Player.name_hash == name_hash, Game.matchup == '1v1').scalar()

        return {"total_games": total_games, "total_wins": total_wins, "total_1v1_games": total_1v1}

    async def async_fetch_player_totals(self, name_hash: str) -> dict:
        '''Async version of fetch_player_totals()'''

        return self.fetch_player_totals(name_hash)

    def fetch_player_rating_stats(self, name_hash: str) -> dict:
        '''Get rating stats of a player.

        Args:
            name_hash: the name_hash of the player.
        '''

        query = text("""
            SELECT 
                name, name_hash, version_code, matchup, \
                rating, wins, total, streak, streak_max, \
                highest, lowest, first_played, last_played
            FROM 
                ratings
            WHERE 
                name_hash = :name_hash
            GROUP BY 
                version_code, matchup;
        """)

        result = self.session.execute(query, {'name_hash': name_hash})
        stats = [tuple(row) for row in result.fetchall()]
        current_time = datetime.now().isoformat()
        return {'stats': stats, 'generated_at': current_time}

    async def async_fetch_player_rating_stats(self, name_hash: str) -> dict:
        '''Async version of fetch_player_rating_stats()'''

        return self.fetch_player_rating_stats(name_hash)

    def fetch_player_recent_games(self, name_hash: str, limit: int = 50) -> dict:
        '''Get recent games of a player.

        Args:
            name_hash: the name_hash of the player.
            limit: maximum number of games to be included.
        '''

        recent_games = self.session.query(Game, Player.rating_change).\
            join(Player, Game.game_guid == Player.game_guid).\
            filter(Player.name_hash == name_hash).\
            order_by(desc(Game.game_time)).\
            limit(limit).\
            all()
        games = [(g.game_guid, g.version_code, g.map_name, g.matchup, g.duration, g.game_time, p)
                 for g, p in recent_games]
        current_time = datetime.now().isoformat()
        return {'games': games, 'generated_at': current_time}

    async def async_fetch_player_recent_games(self, name_hash: str, limit: int = 50) -> dict:
        '''Async version of fetch_player_recent_games()'''

        return self.fetch_player_recent_games(name_hash, limit)

    def search_players_by_name(
            self,
            name: str,
            stype: str = 'std',
            orderby: str = 'nagd',
            page: int = 0,
            page_size: int = 100
    ) -> dict:
        '''Search players by name.

        Args:
            name: the name to search.
            stype: search type. 'std' for standard, 'prefix' for prefix, 'suffix' for suffix, 'exact' for exact match.
            orderby: order by. 'nagd' for name asc, game_count desc, 'gdnd' for game_count desc, name desc, etc.
            page: page number.
            page_size: page size.
        '''

        name = remove_unprintable_chars(name)

        if page < 0 or page_size < 1:
            return {'players': [], 'generated_at': datetime.now().isoformat()}

        order_parts = []
        if len(orderby) < 4:
            order_parts = ["LENGTH(name)", "game_count", "ASC", "DESC"]
        else:
            if orderby[0].lower() == 'g':
                order_parts.extend(["game_count", "LENGTH(name)"])
            else:
                order_parts.extend(["LENGTH(name)", "game_count"])
            if orderby[1].lower() == 'd':
                order_parts.append("DESC")
            else:
                order_parts.append("ASC")
            if orderby[3].lower() == 'd':
                order_parts.append("DESC")
            else:
                order_parts.append("ASC")
        order_cmd = f"{order_parts[0]} {order_parts[2]}, {order_parts[1]} {order_parts[3]}"

        sql = text(f"""
            SELECT name, name_hash, COUNT(game_guid) AS game_count
            FROM players
            WHERE name LIKE :name
            GROUP BY name
            ORDER BY {order_cmd}
            LIMIT :page_size
            OFFSET :page;
        """)

        if stype == 'prefix':
            name = f"{name}%"
        elif stype == 'suffix':
            name = f"%{name}"
        elif stype == 'exact':
            name = f"{name}"
        else:
            name = f"%{name}%"

        players = self.session.execute(
            sql,
            {
                "name": name,
                "page_size": page_size,
                "page": page * page_size
            }
        ).fetchall()
        players = [list(row) for row in players]
        current_time = datetime.now().isoformat()
        return {'players': players, 'generated_at': current_time}

    def search_games(self, criteria: SearchCriteria) -> dict:
        '''Search games.

        Args:
            criteria: Search criteria.

        Note:
            The search criteria is defined in mgxhub/model/searchcriteria.py.
            1) game_guid: GUID of the game. If given, other criteria will be ignored.
        '''
        where_clause = []
        if criteria.game_guid and len(criteria.game_guid) == 32:
            where_clause.append(f"game_guid = '{criteria.game_guid}'")
        else:
            if criteria.duration_min:
                where_clause.append(f"duration >= {criteria.duration_min}")
            if criteria.duration_max:
                where_clause.append(f"duration <= {criteria.duration_max}")
            if criteria.include_ai is not None:
                where_clause.append(f"include_ai = {criteria.include_ai}")
            if criteria.is_multiplayer is not None:
                where_clause.append(f"is_multiplayer = {criteria.is_multiplayer}")
            if criteria.population_min:
                where_clause.append(f"population >= {criteria.population_min}")
            if criteria.population_max:
                where_clause.append(f"population <= {criteria.population_max}")
            if criteria.instruction:
                where_clause.append(f"instruction LIKE '%{criteria.instruction}%'")
            if criteria.gametime_min:
                where_clause.append(f"game_time >= '{criteria.gametime_min * 60}'")
            if criteria.gametime_max:
                where_clause.append(f"game_time <= '{criteria.gametime_max * 60}'")
            if criteria.map_name:
                where_clause.append(f"map_name LIKE '%{criteria.map_name}%'")
            if isinstance(criteria.speed, list) and len(criteria.speed) > 0:
                speed_values = ', '.join(f"'{item}'" for item in criteria.speed)
                where_clause.append(f"speed IN ({speed_values})")
            if isinstance(criteria.victory_type, list) and len(criteria.victory_type) > 0:
                victory_type_values = ', '.join(f"'{item}'" for item in criteria.victory_type)
                where_clause.append(f"victory_type IN ({victory_type_values})")
            if isinstance(criteria.version_code, list) and len(criteria.version_code) > 0:
                version_code_values = ', '.join(f"'{item}'" for item in criteria.version_code)
                where_clause.append(f"version_code IN ({version_code_values.upper()})")
            if isinstance(criteria.matchup, list) and len(criteria.matchup) > 0:
                matchup_values = ', '.join(f"'{item}'" for item in criteria.matchup)
                where_clause.append(f"matchup IN ({matchup_values})")
            if isinstance(criteria.map_size, list) and len(criteria.map_size) > 0:
                map_size_values = ', '.join(f"'{item}'" for item in criteria.map_size)
                where_clause.append(f"map_size IN ({map_size_values})")

        where_clause = " AND ".join(where_clause)
        if where_clause:
            where_clause = f"WHERE {where_clause}"

        if criteria.order_by in ['created', 'duration', 'game_time']:
            order_by = criteria.order_by
        else:
            order_by = 'game_time'
        if criteria.order_desc:
            order_by += " DESC"

        query = text(f"""
            SELECT *
            FROM games
            {where_clause}
            ORDER BY {order_by}
            LIMIT {criteria.page_size}
            OFFSET {criteria.page * criteria.page_size};
        """)
        result = self.session.execute(query)
        games = [list(row) for row in result.fetchall()]
        current_time = datetime.now().isoformat()
        return {'games': games, 'generated_at': current_time}

    def stat_unique_game_options(self) -> dict:
        '''Get unique game options.'''

        query = text("""
            SELECT 'speed' AS column_name, unique_value FROM (SELECT DISTINCT speed AS unique_value FROM games)
            UNION ALL
            SELECT 'victory_type' AS column_name, unique_value FROM (SELECT DISTINCT victory_type AS unique_value FROM games)
            UNION ALL
            SELECT 'version_code' AS column_name, unique_value FROM (SELECT DISTINCT version_code AS unique_value FROM games)
            UNION ALL
            SELECT 'matchup' AS column_name, unique_value FROM (SELECT DISTINCT matchup AS unique_value FROM games)
            UNION ALL
            SELECT 'map_size' AS column_name, unique_value FROM (SELECT DISTINCT map_size AS unique_value FROM games);
        """)

        result = self.session.execute(query).fetchall()
        stats = {}
        for name, optval in result:
            if name not in stats:
                stats[name] = []
            stats[name].append(optval)

        current_time = datetime.now().isoformat()
        return {'stats': stats, 'generated_at': current_time}
