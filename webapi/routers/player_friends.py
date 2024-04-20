'''Fetch close friends of a player'''

from datetime import datetime

from fastapi import Query

from mgxhub import db
from mgxhub.db.operation import get_close_friends as get_close_friends_in_db
from webapi import app


@app.get("/player/friends")
async def get_close_friends(player_hash: str, limit: int = Query(100, gt=0)) -> dict:
    '''Players who played with the given player most.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of players to be included.

    Defined in: `webapi/routers/player_friends.py`
    '''

    session = db()
    players = get_close_friends_in_db(session, player_hash, limit)
    current_time = datetime.now().isoformat()

    return {'players': players, 'generated_at': current_time}
