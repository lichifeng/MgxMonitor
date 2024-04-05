'''Get unique games/players count, new games this month'''

from datetime import datetime, timedelta

from fastapi import BackgroundTasks
from sqlalchemy import func, literal_column, select, union_all

from mgxhub import db
from mgxhub.model.orm import Game, Player
from webapi import app

# pylint: disable=global-statement
# pylint: disable=not-callable

STATS_CACHE = {'cached': None, 'timestamp': 0}


def get_total_stats_raw() -> dict:
    '''Get unique games/players count, new games this month

    Returns:
        A dictionary containing the stats.

    Defined in: `mgxhub/db/operation/stats_index.py`
    '''

    unique_games = select(
        literal_column("'unique_games'").label('stat'),
        func.count(Game.game_guid.distinct()))
    unique_players = select(
        literal_column("'unique_players'").label('stat'),
        func.count(Player.name_hash.distinct()))

    last_month = datetime.now() - timedelta(days=30)
    monthly_games = select(
        literal_column("'monthly_games'").label('stat'),
        func.count(Game.id)).filter(
            func.extract('month', Game.modified) == last_month.month,
            func.extract('year', Game.modified) == last_month.year)

    query = union_all(unique_games, unique_players, monthly_games)

    result = db().execute(query)
    results = result.fetchall()
    stats = dict(results)
    stats['generated_at'] = datetime.now().isoformat()

    STATS_CACHE['cached'] = stats
    STATS_CACHE['timestamp'] = datetime.now()
    return stats


async def get_total_stats_raw_async() -> dict:
    '''Get unique games/players count, new games this month

    Returns:
        A dictionary containing the stats.

    Defined in: `mgxhub/db/operation/stats_index.py`
    '''

    return get_total_stats_raw()


@app.get("/stats/total")
async def get_total_stats(background_tasks: BackgroundTasks) -> dict:
    '''Get unique games/players count, new games this month

    Returns:
        A dictionary containing the stats.

    Defined in: `mgxhub/db/operation/stats_index.py`
    '''

    if STATS_CACHE['cached']:
        if (datetime.now() - STATS_CACHE['timestamp']).seconds > 60:
            background_tasks.add_task(get_total_stats_raw)
        return STATS_CACHE['cached']

    return get_total_stats_raw()
