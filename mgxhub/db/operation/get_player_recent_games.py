'''Get recent games of a player.'''

from sqlalchemy import desc

from mgxhub import db
from mgxhub.model.orm import Game, Player


def get_player_recent_games(name_hash: str, limit: int = 50) -> list:
    '''Get recent games of a player.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of games to be included.

    Defined in: `mgxhub/db/operation/get_player_recent_games.py`
    '''

    recent_games = db().query(Game, Player.rating_change)\
        .join(Player, Game.game_guid == Player.game_guid)\
        .filter(Player.name_hash == name_hash)\
        .order_by(desc(Game.game_time))\
        .limit(limit)\
        .all()

    return [(g.game_guid, g.version_code, g.map_name, g.matchup, g.duration, g.game_time, p) for g, p in recent_games]


async def async_get_player_recent_games(name_hash: str, limit: int = 50) -> list:
    '''Async version of fetch_player_recent_games()'''

    return get_player_recent_games(name_hash, limit)
