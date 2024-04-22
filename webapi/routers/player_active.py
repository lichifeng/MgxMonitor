'''Fetch active players. The simple version.'''


from fastapi import Depends, Query
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.db.operation import get_active_players_async
from webapi import app


@app.get("/player/active", tags=['player'])
async def get_active_players(
    limit: int = Query(20, ge=1),
    days: int = Query(30, ge=0),
    db: Session = Depends(db_dep)
) -> dict:
    '''Fetch active players.

    Including name, name_hash, and the number of games played in the last N days.

    Args:
        limit: maximum number of players to be included.
        days: number of days to look back.

    Defined in: `webapi/routers/player_active.py`
    '''

    result = await get_active_players_async(db, limit, days)

    return result
