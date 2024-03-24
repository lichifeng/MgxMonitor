'''Fetch active players. The simple version.'''


from datetime import datetime, timedelta

from fastapi import Query
from sqlalchemy import desc, func

from mgxhub import db
from mgxhub.model.orm import Player
from webapi import app

# pylint: disable=E1102


@app.get("/player/active")
async def get_active_players(limit: int = Query(20, ge=1), days: int = Query(30, ge=0)) -> dict:
    '''Newly found players.

    Defined in: `webapi/routers/player_active.py`
    '''

    x_days_ago = datetime.now() - timedelta(days=days)

    result = db().query(
        Player.name, Player.name_hash, func.count(Player.id).label('count')
    ).filter(
        Player.created >= x_days_ago
    ).group_by(
        Player.name
    ).order_by(
        desc('count')
    ).limit(limit).all()

    players = [(row[0], row[1], row[2]) for row in result]

    return {"players": players, "threshold_date": x_days_ago.isoformat()}
