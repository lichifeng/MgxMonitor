'''Get option for speed, victory type, version code, matchup, map size, etc.'''

from datetime import datetime

from sqlalchemy import text

from mgxhub import db
from webapi import app


@app.get("/game/optionstats")
async def get_game_option_stats() -> dict:
    '''Get option for speed, victory type, version code, matchup, map size, etc.

    Returns:
        A dictionary containing the option stats.

    Defined in: `mgxhub/db/operation/game_optionstats.py`
    '''

    query = text("""
        SELECT 'speed' AS column_name, unique_value FROM (SELECT DISTINCT speed AS unique_value FROM games)
        UNION ALL
        SELECT 'victory_type' AS column_name, unique_value FROM (SELECT DISTINCT victory_type AS unique_value FROM games)
        UNION ALL
        SELECT 'version_code' AS column_name, unique_value FROM (SELECT DISTINCT version_code AS unique_value FROM games)
        UNION ALL
        SELECT 'matchup' AS column_name, unique_value FROM (SELECT DISTINCT matchup AS unique_value FROM games)
        UNION ALL
        SELECT 'map_size' AS column_name, unique_value FROM (SELECT DISTINCT map_size AS unique_value FROM games);
    """)

    result = db().execute(query).fetchall()
    stats = {}
    for name, optval in result:
        if not optval:
            continue

        if name not in stats:
            stats[name] = []

        stats[name].append(optval)

    current_time = datetime.now().isoformat()

    return {'stats': stats, 'generated_at': current_time}
