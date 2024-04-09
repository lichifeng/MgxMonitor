'''Get recent games of a player.'''

from sqlalchemy import desc
from sqlalchemy.orm import Session

from mgxhub.model.orm import Game, Player


def get_player_recent_games(session: Session, name_hash: str, limit: int = 50, offset: int = 0) -> list:
    '''Get recent games of a player.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of games to be included.

    Defined in: `mgxhub/db/operation/get_player_recent_games.py`
    '''

    recent_games = session.query(Game, Player.rating_change)\
        .join(Player, Game.game_guid == Player.game_guid)\
        .filter(Player.name_hash == name_hash)\
        .order_by(desc(Game.game_time))\
        .offset(offset)\
        .limit(limit)\
        .all()

    return [(g.game_guid, g.version_code, g.map_name, g.matchup, g.duration, g.game_time, p) for g, p in recent_games]


async def async_get_player_recent_games(session: Session, name_hash: str, limit: int = 50, offset: int = 0) -> list:
    '''Async version of fetch_player_recent_games()'''

    return get_player_recent_games(session, name_hash, limit, offset)
