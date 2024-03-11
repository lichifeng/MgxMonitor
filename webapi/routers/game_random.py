'''Fetch random games'''

from datetime import datetime

from sqlalchemy import text

from mgxhub import db
from webapi import app


@app.get("/game/random")
async def fetch_rand_games(threshold: int = 10, limit: int = 50) -> dict:
    '''Fetch random games

    - **threshold**: Minimum duration of the game, in minutes. Default is 10.
    - **limit**: Maximum number of games to fetch. Default is 50.

    Defined in: `webapi/routers/game_random.py`
    '''

    query = text("""
        SELECT 
            game_guid, version_code, created, map_name, matchup, duration, speed 
        FROM games 
        WHERE duration > :threshold 
        ORDER BY RANDOM()
        LIMIT :limit;
    """)

    result = db().execute(query, {'threshold': threshold * 60, 'limit': limit})
    games = [list(row) for row in result.fetchall()]
    current_time = datetime.now().isoformat()
    return {'games': games, 'generated_at': current_time}
