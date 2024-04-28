'''Get recent games of a player'''

from datetime import datetime

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.db.operation import get_player_recent_games
from webapi import app


@app.get("/player/recent_games", tags=['player'])
async def get_player_games(
    player_hash: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1),
    lang: str = 'en',
    db: Session = Depends(db_dep)
) -> dict:
    '''Get recent games of a player

    Args:
        player_hash: MD5 hash of the player's name.
        page: page number.
        page_size: number of games per page.

    Defined in: `webapi/routers/player_recent_game.py`
    '''

    games = get_player_recent_games(db, player_hash, page_size, (page - 1) * page_size, lang)

    current_time = datetime.now().isoformat()

    return {
        'games': games,
        'generated_at': current_time
    }
