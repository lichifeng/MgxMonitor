'''Fetch close friends of a player'''

from datetime import datetime

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.db.operation import get_close_friends as get_close_friends_in_db
from webapi import app


@app.get("/player/friends", tags=['player'])
async def get_close_friends(
    player_hash: str,
    limit: int = Query(100, gt=0),
    db: Session = Depends(db_dep)
) -> dict:
    '''Players who played with the given player most.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of players to be included.

    Defined in: `webapi/routers/player_friends.py`
    '''

    players = get_close_friends_in_db(db, player_hash, limit)
    current_time = datetime.now().isoformat()

    return {'players': players, 'generated_at': current_time}
