'''Fetch latest N players and their simple stats.'''


from datetime import datetime

from sqlalchemy import text

from mgxhub import db
from webapi import app


@app.get("/player/latest")
async def get_latest_players(limit: int = 20) -> dict:
    '''Newly found players.

    Including won games, total games, and 1v1 games counts.

    Args:
        limit: maximum number of players to be included.

    Defined in: `webapi/routers/player_latest.py`
    '''

    query = text("""
        SELECT 
            ep.name, 
            ep.latest_created, 
            (SELECT COUNT(*) FROM players WHERE name = ep.name AND is_winner = 1) AS win_count,
            (SELECT COUNT(*) FROM players WHERE name = ep.name) AS total_games,
            (SELECT COUNT(*) FROM games g JOIN players p ON g.game_guid = p.game_guid WHERE p.name = ep.name AND g.matchup = '1v1') AS total_1v1_games
        FROM 
            (SELECT 
                name,
                MAX(created) AS latest_created
            FROM 
                players
            GROUP BY 
                name
            LIMIT :limit) AS ep
        ORDER BY 
            ep.latest_created DESC;
    """)

    result = db().execute(query, {'limit': limit})
    players = [list(row) for row in result.fetchall()]

    current_time = datetime.now().isoformat()
    return {'players': players, 'generated_at': current_time}
