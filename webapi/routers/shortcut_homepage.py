'''Shortcut for homepage data of aocrec.com'''

import asyncio
import json

from fastapi import Depends, Query, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from mgxhub.cacher import Cacher
from mgxhub.db import db_dep
from mgxhub.db.operation import (fetch_latest_games_async,
                                 get_active_players_async,
                                 get_total_stats_raw_async)
from webapi import app


async def gen_homepage_data(db: Session, glimit: int = 5, plimit: int = 30, pdays: int = 30) -> str:
    '''Generate homepage data of aocrec.com'''

    results = await asyncio.gather(
        fetch_latest_games_async(db, glimit),
        get_active_players_async(db, plimit, pdays),
        get_total_stats_raw_async(db)
    )

    return json.dumps(jsonable_encoder({
        "latest_games": results[0],
        "active_players": results[1],
        "total_stats": results[2]
    }))


@app.get("/shortcut/homepage", tags=['stats'])
async def fetch_homepage_data(
    glimit: int = Query(5, ge=1),
    plimit: int = Query(30, ge=1),
    pdays: int = Query(30, ge=1),
    db: Session = Depends(db_dep)
) -> str:
    '''Shortcut for homepage data of aocrec.com

    Defined in: `webapi/routers/shortcut_homepage.py`
    '''

    cache_key = f"homepage_data_{glimit}_{plimit}_{pdays}"
    cacher = Cacher(db)
    cached = cacher.get(cache_key)
    if cached:
        return Response(content=cached, media_type="application/json", headers={"X-From-Cache": "true"})

    result = await gen_homepage_data(db, glimit, plimit, pdays)

    cacher.set(cache_key, result)

    return Response(content=result, media_type="application/json")
