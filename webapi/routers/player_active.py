'''Fetch active players. The simple version.'''


from fastapi import Query

from mgxhub import db
from mgxhub.db.operation import get_active_players_async
from webapi import app


@app.get("/player/active")
async def get_active_players(limit: int = Query(20, ge=1), days: int = Query(30, ge=0)) -> dict:
    '''Fetch active players.

    Including name, name_hash, and the number of games played in the last N days.

    Args:
        limit: maximum number of players to be included.
        days: number of days to look back.

    Defined in: `webapi/routers/player_active.py`
    '''

    session = db()
    return await get_active_players_async(session, limit, days)
