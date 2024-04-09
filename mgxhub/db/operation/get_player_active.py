from datetime import datetime, timedelta

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from mgxhub.model.orm import Player

# pylint: disable=E1102


async def get_active_players_async(session: Session, limit: int, days: int) -> dict:
    '''Newly found players.

    Defined in: `webapi/routers/player_active.py`
    '''

    x_days_ago = datetime.now() - timedelta(days=days)

    result = session.query(
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
