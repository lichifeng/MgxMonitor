'''Fetch recently uploaded games'''


from fastapi import Depends, Query
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.db.operation.get_games_latest import fetch_latest_games_async
from webapi import app


@app.get("/game/latest", tags=['game'])
async def fetch_latest_games(limit: int = Query(100, gt=0), db: Session = Depends(db_dep)) -> dict:
    '''Fetch recently uploaded games

    - **limit**: The number of games to fetch. Default is 100.

    Returned data format:
        [game_guid, version_code, created_time, game_time, map_name, matchup, duration, speed, uploader]

    Defined in: `webapi/routers/game_latest.py`
    '''

    latest_games = await fetch_latest_games_async(db, limit)
    return latest_games
