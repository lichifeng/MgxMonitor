'''Get option values like 1v1, 2v2, 3v3, AOC10, AOC10C, etc.'''

import json

from fastapi import Depends, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from mgxhub.cacher import Cacher
from mgxhub.db import db_dep
from mgxhub.model.orm import Game
from webapi import app

# pylint: disable=not-callable


@app.get("/optionvalues", tags=['game'])
async def get_option_values(session: Session = Depends(db_dep)) -> dict:
    '''Get option values like 1v1, 2v2, 3v3, AOC10, AOC10C, etc.

    Returns:
        A dictionary containing the option values.

    Defined in: `mgxhub/db/operation/get_option_values.py`
    '''

    cacher = Cacher(session)
    cached = cacher.get('option_values')
    if cached:
        return Response(content=cached, media_type="application/json", headers={"X-From-Cache": "true"})

    def get_counts(session: Session, column):
        return session.query(
            column, func.count(column).label('count')
        ).group_by(
            column
        ).order_by(desc('count')).all()

    matchups = get_counts(session, Game.matchup)
    versions = get_counts(session, Game.version_code)
    mapsizes = get_counts(session, Game.map_size)
    speeds = get_counts(session, Game.speed)

    result = json.dumps(jsonable_encoder({
        'matchups': dict(matchups),
        'versions': dict(versions),
        'mapsizes': dict(mapsizes),
        'speeds': dict(speeds)
    }))

    cacher.set('option_values', result)

    return Response(content=result, media_type="application/json")
