'''Get rating statistics of different versions'''

import json
from datetime import datetime

from fastapi import Depends, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from mgxhub.cacher import Cacher
from mgxhub.db import db_dep
from mgxhub.db.operation import get_rating_stats
from webapi import app


@app.get("/rating/stats", tags=['rating'])
async def get_rating_meta(db: Session = Depends(db_dep)) -> str:
    '''Get rating statistics of different versions.

    Used in ratings page to show the number of rating records for each version.

    Defined in: `webapi/routers/rating_stats.py`
    '''

    cacher = Cacher(db)
    cached = cacher.get('rating_stats')
    if cached:
        return Response(content=cached, media_type="application/json")

    current_time = datetime.now().isoformat()
    result = json.dumps(jsonable_encoder({'stats': get_rating_stats(db), 'generated_at': current_time}))
    cacher.set('rating_stats', result)

    return Response(content=result, media_type="application/json")
