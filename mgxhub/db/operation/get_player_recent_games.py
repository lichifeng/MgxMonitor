'''Get recent games of a player.'''

import gettext

from sqlalchemy import desc
from sqlalchemy.orm import Session

from mgxhub.model.orm import Game, Player


def get_player_recent_games(db: Session, name_hash: str, limit: int = 50, offset: int = 0, lang: str = 'en') -> list:
    '''Get recent games of a player.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of games to be included.

    Defined in: `mgxhub/db/operation/get_player_recent_games.py`
    '''

    recent_games = db.query(Game, Player.rating_change)\
        .join(Player, Game.game_guid == Player.game_guid)\
        .filter(Player.name_hash == name_hash)\
        .group_by(Game.game_guid)\
        .order_by(desc(Game.game_time))\
        .offset(offset)\
        .limit(limit)\
        .all()

    t = gettext.translation(lang, localedir='translations', languages=["en"], fallback=True)
    _ = t.gettext

    return [(g.game_guid, g.version_code, _(g.map_name), g.matchup, g.duration, g.game_time, p, [[_.name, _.name_hash] for _ in g.players]) for g, p in recent_games]


async def async_get_player_recent_games(db: Session, name_hash: str, limit: int = 50, offset: int = 0, lang: str = 'en') -> list:
    '''Async version of fetch_player_recent_games()'''

    return get_player_recent_games(db, name_hash, limit, offset, lang)
