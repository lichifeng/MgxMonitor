'''Find players who played with the given player most.'''

from sqlalchemy import alias, desc, func

from mgxhub import db
from mgxhub.model.orm import Player

# pylint: disable=not-callable


def get_close_friends(name_hash: str, limit: int = 100) -> list:
    '''Players who played with the given player most.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of players to be included.

    Defined in: `mgxhub/db/operation/find_player_friends.py`
    '''

    Friend = alias(Player, name='p2')

    query = (
        db().query(
            Friend.c.name,
            func.count('*').label('common_games_count')
        )
        .select_from(Player)
        .join(
            Friend, Player.game_guid == Friend.c.game_guid
        )
        .filter(
            Player.name_hash == name_hash,
            Player.name != Friend.c.name
        )
        .group_by(Friend.c.name)
        .order_by(desc('common_games_count'))
        .limit(limit)
    )

    result = query.all()
    return [[row.name, row.common_games_count] for row in result]


async def async_get_close_friends(name_hash: str, limit: int = 100) -> list:
    '''Async version of find_close_friends()'''

    return get_close_friends(name_hash, limit)
