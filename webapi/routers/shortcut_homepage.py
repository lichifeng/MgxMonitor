'''Shortcut for homepage data of aocrec.com'''

import asyncio

from fastapi import Query

from mgxhub import db
from mgxhub.db.operation import (fetch_latest_games_async,
                                 get_active_players_async)
from webapi import app
from webapi.routers.stats_total import get_total_stats_raw_async


@app.get("/shortcut/homepage")
async def fetch_homepage_data(
    glimit: int = Query(5, ge=1),
    plimit: int = Query(30, ge=1),
    pdays: int = Query(30, ge=1)
) -> dict:
    '''Shortcut for homepage data of aocrec.com

    Defined in: `webapi/routers/shortcut_homepage.py`
    '''

    session = db()
    results = await asyncio.gather(
        fetch_latest_games_async(session, glimit),
        get_active_players_async(session, plimit, pdays),
        get_total_stats_raw_async(session)
    )

    # 返回结果
    return {
        "latest_games": results[0],
        "active_players": results[1],
        "total_stats": results[2]
    }
