'''Router for the player profile endpoint'''

import asyncio

from mgxhub.db.operation import (async_get_close_friends,
                                 async_get_player_rating_stats,
                                 async_get_player_recent_games,
                                 async_get_player_totals)
from webapi import app


@app.get("/player/profile")
async def get_player_comprehensive(player_hash: str) -> dict:
    '''Fetch comprehensive information of a player

    Args:
        player_hash: MD5 hash of the player's name.

    Defined in: `webapi/routers/player_profile.py`
    '''

    result = await asyncio.gather(
        async_get_player_totals(player_hash),
        async_get_player_rating_stats(player_hash),
        async_get_player_recent_games(player_hash),
        async_get_close_friends(player_hash)
    )

    return {
        "totals": result[0],
        "ratings": result[1],
        "recent_games": result[2],
        "close_friends": result[3]
    }
