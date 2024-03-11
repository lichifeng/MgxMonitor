'''Fetch close friends of a player'''

from datetime import datetime

from mgxhub.db.operation.find_player_friends import get_close_friends
from webapi import app


@app.get("/player/friends")
async def get_close_friends(player_hash: str, limit: int = 100) -> dict:
    '''Players who played with the given player most.

    Args:
        name_hash: the name_hash of the player.
        limit: maximum number of players to be included.

    Defined in: `webapi/routers/player_friends.py`
    '''

    players = get_close_friends(player_hash, limit)

    current_time = datetime.now().isoformat()
    return {'players': players, 'generated_at': current_time}
