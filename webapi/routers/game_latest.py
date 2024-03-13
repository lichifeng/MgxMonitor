'''Fetch recently uploaded games'''

from datetime import datetime

from fastapi import Query
from sqlalchemy import text

from mgxhub import db
from webapi import app


@app.get("/game/latest")
async def fetch_latest_games(limit: int = Query(100, gt=0)) -> dict:
    '''Fetch recently uploaded games

    - **limit**: The number of games to fetch. Default is 100.

    Returned data format:
        [game_guid, version_code, created_time, game_time, map_name, matchup, duration, speed, uploader]

    Defined in: `webapi/routers/game_latest.py`
    '''

    query = text("""
        WITH latest_games AS (
            SELECT 
                g.game_guid, g.version_code, g.created, g.game_time, g.map_name, g.matchup, g.duration, g.speed, f.recorder_slot
            FROM 
                (SELECT * FROM games ORDER BY created DESC LIMIT :limit) AS g
            JOIN 
                files AS f ON g.game_guid = f.game_guid
            WHERE 
                f.created = (SELECT MIN(created) FROM files WHERE game_guid = g.game_guid)
        )
        SELECT latest_games.*, p.name 
        FROM latest_games
        JOIN players AS p ON latest_games.game_guid = p.game_guid AND latest_games.recorder_slot = p.slot;
    """)

    result = db().execute(query, {'limit': limit})
    games = [list(row) for row in result.fetchall()]
    current_time = datetime.now().isoformat()

    return {'games': games, 'generated_at': current_time}
