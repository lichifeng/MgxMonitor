'''Get rating stats of a player'''

from mgxhub import db
from mgxhub.model.orm import Rating

# pylint: disable=not-callable


def get_player_rating_stats(name_hash: str) -> list:
    '''Get rating stats of a player, grouped by version_code and matchup.

    Args:
        name_hash: the name_hash of the player.

    Defined in: `mgxhub/db/operation/get_player_rating_stats.py`
    '''

    result = db().query(
        Rating.name, Rating.name_hash, Rating.version_code, Rating.matchup,
        Rating.rating, Rating.highest, Rating.lowest, Rating.wins, Rating.total,
        Rating.streak, Rating.streak_max, Rating.first_played, Rating.last_played
    ).filter(
        Rating.name_hash == name_hash
    ).group_by(
        Rating.version_code, Rating.matchup
    ).all()

    return [tuple(row) for row in result]


async def async_get_player_rating_stats(name_hash: str) -> list:
    '''Async version of fetch_player_rating_stats()'''

    return get_player_rating_stats(name_hash)
