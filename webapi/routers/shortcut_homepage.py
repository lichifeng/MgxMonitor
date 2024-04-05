'''Shortcut for homepage data of aocrec.com'''

import asyncio

from fastapi import Query

from webapi import app
from webapi.routers.game_latest import fetch_latest_games_raw_async
from webapi.routers.player_active import get_active_players_raw_async
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

    # 并发运行所有的异步操作
    results = await asyncio.gather(
        fetch_latest_games_raw_async(glimit),
        get_active_players_raw_async(plimit, pdays),
        get_total_stats_raw_async()
    )

    # 返回结果
    return {
        "latest_games": results[0],
        "active_players": results[1],
        "total_stats": results[2]
    }
