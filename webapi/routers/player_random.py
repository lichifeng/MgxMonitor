'''Random player router'''

from datetime import datetime
from hashlib import md5

from sqlalchemy import text

from mgxhub import db
from webapi import app


@app.get("/player/random")
async def get_rand_players(threshold: int = 10, limit: int = 300) -> dict:
    '''Fetch random players and their game counts

    Including total games of each player. Used mainly in player cloud.

    Args:
        threshold: minimum games of a player to be included.
        limit: maximum number of players to be included. Max is 1000.

    Returns:
        A dictionary containing a list of players and their game counts.

    Defined in: `webapi/routers/player_random.py`
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

    result = db().execute(query, {'threshold': threshold, 'limit': limit})
    players = [{
        'name': row.name,
        'name_hash': md5(str(row.name).encode('utf-8')).hexdigest(),
        'game_count': row.game_count
    } for row in result]

    current_time = datetime.now().isoformat()
    return {'players': players, 'generated_at': current_time}
