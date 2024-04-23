'''Get unique games/players count, new games this month'''

import json

from fastapi import Depends, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from mgxhub.cacher import Cacher
from mgxhub.db import db_dep
from mgxhub.db.operation import get_total_stats_raw
from webapi import app


@app.get("/stats/total", tags=['stats'])
async def get_total_stats(db: Session = Depends(db_dep)) -> str:
    '''Get unique games/players count, new games this month

    Returns:
        A dictionary containing the stats.

    Defined in: `mgxhub/db/operation/stats_index.py`
    '''

    cacher = Cacher(db)

    cached = cacher.get('total_stats')
    if cached:
        return Response(content=cached, media_type="application/json")

    stats = get_total_stats_raw(db)
    result = json.dumps(jsonable_encoder(stats))

    cacher.set('total_stats', result)

    return Response(content=result, media_type="application/json")
