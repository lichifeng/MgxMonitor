'''Find players who played with the given player most.'''

from sqlalchemy import text

from mgxhub import db


def get_close_friends(name_hash: str, limit: int = 100) -> list:
    '''Players who played with the given player most.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of players to be included.

    Defined in: `mgxhub/db/operation/find_player_friends.py`
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

    result = db().execute(query, {'name_hash': name_hash, 'limit': limit})
    return [list(row) for row in result.fetchall()]


async def async_get_close_friends(name_hash: str, limit: int = 100) -> list:
    '''Async version of find_close_friends()'''

    return get_close_friends(name_hash, limit)
