'''Get stats of total games/players, etc.'''

from datetime import datetime

from sqlalchemy import func, literal_column, select, union_all
from sqlalchemy.orm import Session

from mgxhub.model.orm import Game, Player

# pylint: disable=E1102


def get_total_stats_raw(db: Session) -> dict:
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

    current_time = datetime.now()
    current_month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_games = select(
        literal_column("'monthly_games'").label('stat'),
        func.count(Game.id)).filter(Game.created >= current_month_start)

    query = union_all(unique_games, unique_players, monthly_games)

    result = db.execute(query)
    results = result.fetchall()
    stats = dict(results)

    stats['generated_at'] = datetime.now().isoformat()

    return stats


async def get_total_stats_raw_async(db: Session) -> dict:
    '''Get unique games/players count, new games this month

    Returns:
        A dictionary containing the stats.

    Defined in: `mgxhub/db/operation/stats_index.py`
    '''

    return get_total_stats_raw(db)
