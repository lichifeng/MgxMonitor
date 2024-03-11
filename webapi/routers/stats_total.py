'''Get unique games/players count, new games this month'''

from datetime import datetime

from sqlalchemy import text

from mgxhub import db
from webapi import app


@app.get("/stats/total")
async def get_total_stats() -> dict:
    '''Get unique games/players count, new games this month

    Returns:
        A dictionary containing the stats.

    Defined in: `mgxhub/db/operation/stats_index.py`
    '''

    query = text("""
        SELECT 'unique_games', COUNT(DISTINCT game_guid) AS count FROM games
        UNION ALL
        SELECT 'unique_players', COUNT(DISTINCT name_hash) FROM players
        UNION ALL
        SELECT 'monthly_games', COUNT(*) FROM games WHERE strftime('%m', modified) = strftime('%m', datetime('now', '-1 month')) AND strftime('%Y', modified) = strftime('%Y', 'now')
    """)

    result = db().execute(query)
    results = result.fetchall()
    stats = dict(results)

    # Add the current time to the stats
    stats['generated_at'] = datetime.now().isoformat()

    return stats
