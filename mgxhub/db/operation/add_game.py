'''Add a game to the database'''

from datetime import datetime
from hashlib import md5

from sqlalchemy import and_
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from mgxhub import logger
from mgxhub.model.orm import Chat, File, Game, Player
from mgxhub.util import sanitize_playername


def _update_gametime(session: Session, game: Game, game_time: datetime) -> bool:
    '''Update the game time of a game.

    Args:
        game_guid: GUID of the game.
        game_time: New game time.

    Returns:
        True if the game time is updated, False otherwise.

    Defined in: `mgxhub/db/operation/add_game.py`
    '''

    if game:
        game.game_time = game_time
        session.commit()
        logger.info(f'[DB] game_time updated: {game.game_guid}')
        return True
    return False


def add_game(session: Session, d: dict, t: str | None = None, source: str = "") -> tuple[str, str]:
    '''Add a game to the database.

    Args:
        d: Game data from the parser.
        t: Time of the game played. Normall last modified time of the actually record file in ISO format. 
        source: Source of the record file. User uploaded from web, or from the bot, etc. 

    Returns:
        A tuple of two strings. The first string is the status of the operation,
        which is one of "exists", "invalid", "success", "duplicated", "updated".
        The second string is the GUID of the game. 

    Defined in: `mgxhub/db/operation/add_game.py`
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

    game = session.query(Game).filter(Game.game_guid == d.get('guid')).first()
    if game and isinstance(game.duration, (int, float)):
        update_gametime = False
        if hasattr(game, 'game_time') and game_time < game.game_time:
            game.game_time = game_time
            update_gametime = True

        # Even if the game exists, updating the game time still makes sense.
        # Longer records may had lost the original creation time while short ones not.
        if game.duration > d.get('duration'):
            if update_gametime:
                _update_gametime(session, game, game_time)
            return "exists", game.game_guid
        if game.duration == d.get('duration'):
            same_file = session.query(File).filter(File.md5 == d.get('md5')).first()
            if same_file:
                if update_gametime:
                    _update_gametime(session, game, game_time)
                return "duplicated", game.game_guid

    merged_game = session.merge(Game(
        id=game.id if game else None,
        game_guid=d.get('guid'),
        duration=d.get('duration'),
        include_ai=d.get('includeAI'),
        is_multiplayer=d.get('isMultiplayer'),
        population=d.get('population'),
        speed=d.get('speedEn'),
        matchup=d.get('matchup'),
        map_name=d.get('map', {}).get('nameEn', d.get('map', {}).get('name')),
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

    players = d.get('players')
    if players:
        for p in players:
            if p.get('name'):
                sanitized_name = sanitize_playername(p.get('name')) or '<NULL>'
            else:
                sanitized_name = '<NULL>'

            init_position = p.get('initPosition', [-1, -1])
            player = session.query(Player).filter(
                and_(Player.game_guid == d.get('guid'), Player.slot == p.get('slot'))).first()
            if player is None:
                player = Player()

            player.game_guid = d.get('guid')
            player.slot = p.get('slot')
            player.index_player = p.get('index')
            player.name = sanitized_name
            player.name_hash = md5(sanitized_name.encode('utf-8')).hexdigest()
            player.type = p.get('typeEn')
            player.team = p.get('team')
            player.color_index = p.get('colorIndex')
            player.init_x = init_position[0] if len(init_position) > 0 else -1
            player.init_y = init_position[1] if len(init_position) > 1 else -1
            player.disconnected = p.get('disconnected')
            player.is_winner = p.get('isWinner')
            player.is_main_operator = p.get('mainOp')
            player.civ_id = p.get('civilization', {}).get('id')
            player.civ_name = p.get('civilization', {}).get('nameEn')
            player.feudal_time = p.get('feudalTime')
            player.castle_time = p.get('castleTime')
            player.imperial_time = p.get('imperialTime')
            player.resigned_time = p.get('resigned')

            session.add(player)

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
        source=source,
        realsize=d.get('realsize')
    )
    session.add(record_file)

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
            session.execute(stmt)

    session.commit()

    if game:
        return "updated", merged_game.game_guid
    return "success", merged_game.game_guid
