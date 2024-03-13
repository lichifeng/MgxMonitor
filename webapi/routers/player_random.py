'''Random player router'''

from datetime import datetime
from hashlib import md5

from fastapi import BackgroundTasks, Query
from sqlalchemy import func, select, text

from mgxhub import db
from mgxhub.model.orm import Player
from webapi import app

# pylint: disable=not-callable

RANDOM_CACHE = {"cached": None, "lock": False}


def _get_rand_players(threshold: int, limit: int) -> None:
    '''Fetch random players and their game counts

    Including total games of each player. Used mainly in player cloud.

    Args:
        threshold: minimum games of a player to be included.
        limit: maximum number of players to be included. Max is 1000.

    Returns:
        A list of players and their game counts.

    Defined in: `webapi/routers/player_random.py`
    '''

    if RANDOM_CACHE['lock']:
        return

    RANDOM_CACHE['lock'] = True

    subquery = select(
        Player.name,
        func.count(Player.game_guid).label('game_count')
    ).group_by(
        Player.name
    ).having(
        text("game_count > :threshold")
    ).params(
        threshold=threshold
    ).subquery()

    query = db().query(
        subquery.c.name,
        subquery.c.game_count
    ).order_by(
        func.random()
    ).limit(limit)

    result = query.all()

    players = [{
        'name': row.name,
        'name_hash': md5(str(row.name).encode('utf-8')).hexdigest(),
        'game_count': row.game_count
    } for row in result]

    RANDOM_CACHE['cached'] = players
    RANDOM_CACHE['lock'] = False


@app.get("/player/random")
async def get_rand_players(
    background_tasks: BackgroundTasks,
    threshold: int = Query(10, gt=0),
    limit: int = Query(300, gt=0)
) -> dict:
    '''Fetch random players and their game counts

    Including total games of each player. Used mainly in player cloud.

    Args:
        threshold: minimum games of a player to be included.
        limit: maximum number of players to be included. Max is 1000.

    Returns:
        A dictionary containing a list of players and their game counts.

    Defined in: `webapi/routers/player_random.py`
    '''

    current_time = datetime.now().isoformat()
    if RANDOM_CACHE['cached']:
        background_tasks.add_task(_get_rand_players, threshold, limit)
        return {
            'players': RANDOM_CACHE['cached'],
            'generated_at': current_time
        }

    _get_rand_players(threshold, limit)
    return {
        'players': RANDOM_CACHE['cached'],
        'generated_at': current_time
    }
