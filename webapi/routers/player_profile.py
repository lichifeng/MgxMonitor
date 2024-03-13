'''Router for the player profile endpoint'''

import asyncio

from fastapi import Query

from mgxhub.db.operation import (async_get_close_friends,
                                 async_get_player_rating_stats,
                                 async_get_player_recent_games,
                                 async_get_player_totals)
from webapi import app


@app.get("/player/profile")
async def get_player_comprehensive(
    player_hash: str,
    recent_limit: int = Query(50, gt=0),
    friend_limit: int = Query(50, gt=0)
) -> dict:
    '''Fetch comprehensive information of a player

    Args:
        player_hash: MD5 hash of the player's name.
        recent_limit: Maximum number of recent games to be included.
        friend_limit: Maximum number of close friends to be included.

    Defined in: `webapi/routers/player_profile.py`
    '''

    result = await asyncio.gather(
        async_get_player_totals(player_hash),
        async_get_player_rating_stats(player_hash),
        async_get_player_recent_games(player_hash, recent_limit),
        async_get_close_friends(player_hash, friend_limit)
    )

    return {
        "totals": result[0],
        "ratings": result[1],
        "recent_games": result[2],
        "close_friends": result[3]
    }
