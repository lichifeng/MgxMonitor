'''Router for the player profile endpoint'''

import asyncio

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.db.operation import (async_get_close_friends,
                                 async_get_player_rating_stats,
                                 async_get_player_recent_games,
                                 async_get_player_totals)
from mgxhub.model.orm import Player
from webapi import app


async def hash2name(db: Session, player_hash: str) -> str:
    '''Convert player hash to name'''
    found = db.query(Player.name).filter(Player.name_hash == player_hash).first()
    return found[0] if found else None


@app.get("/player/profile", tags=['player'])
async def get_player_comprehensive(
    player_hash: str,
    recent_limit: int = Query(50, gt=0),
    friend_limit: int = Query(50, gt=0),
    db: Session = Depends(db_dep)
) -> dict:
    '''Fetch comprehensive information of a player

    Args:
        player_hash: MD5 hash of the player's name.
        recent_limit: Maximum number of recent games to be included.
        friend_limit: Maximum number of close friends to be included.

    Defined in: `webapi/routers/player_profile.py`
    '''

    result = await asyncio.gather(
        async_get_player_totals(db, player_hash),
        async_get_player_rating_stats(db, player_hash),
        async_get_player_recent_games(db, player_hash, recent_limit),
        async_get_close_friends(db, player_hash, friend_limit),
        hash2name(db, player_hash)
    )

    return {
        "totals": result[0],
        "ratings": result[1],
        "recent_games": result[2],
        "close_friends": result[3],
        "name": result[4]
    }
