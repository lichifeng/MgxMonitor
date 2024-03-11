'''Get rating stats of a player'''

from sqlalchemy import text

from mgxhub import db


def get_player_rating_stats(name_hash: str) -> list:
    '''Get rating stats of a player, grouped by version_code and matchup.

    Args:
        name_hash: the name_hash of the player.

    Defined in: `mgxhub/db/operation/get_player_rating_stats.py`
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

    result = db().execute(query, {'name_hash': name_hash})
    return [tuple(row) for row in result.fetchall()]


async def async_get_player_rating_stats(name_hash: str) -> list:
    '''Async version of fetch_player_rating_stats()'''

    return get_player_rating_stats(name_hash)
