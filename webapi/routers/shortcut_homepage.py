'''Shortcut for homepage data of aocrec.com'''

import asyncio

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.db.operation import (fetch_latest_games_async,
                                 get_active_players_async)
from webapi import app
from webapi.routers.stats_total import get_total_stats_raw_async


@app.get("/shortcut/homepage", tags=['stats'])
async def fetch_homepage_data(
    glimit: int = Query(5, ge=1),
    plimit: int = Query(30, ge=1),
    pdays: int = Query(30, ge=1),
    db: Session = Depends(db_dep)
) -> dict:
    '''Shortcut for homepage data of aocrec.com

    Defined in: `webapi/routers/shortcut_homepage.py`
    '''

    results = await asyncio.gather(
        fetch_latest_games_async(db, glimit),
        get_active_players_async(db, plimit, pdays),
        get_total_stats_raw_async()
    )

    return {
        "latest_games": results[0],
        "active_players": results[1],
        "total_stats": results[2]
    }
