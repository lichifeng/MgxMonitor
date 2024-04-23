'''Get option for speed, victory type, version code, matchup, map size, etc.'''

import json
from datetime import datetime

from fastapi import Depends, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from mgxhub.cacher import Cacher
from mgxhub.db import db_dep
from mgxhub.model.orm import Game
from webapi import app


@app.get("/game/optionstats", tags=['game'])
async def get_game_option_stats(db: Session = Depends(db_dep)) -> str:
    '''Get option for speed, victory type, version code, matchup, map size, etc.

    Returns:
        A dictionary containing the option stats.

    Defined in: `webapi/routers/game_optionstats.py`
    '''

    cacher = Cacher(db)

    cached = cacher.get('game_option_stats')
    if cached:
        return Response(content=cached, media_type="application/json")

    def get_distinct_values(column):
        return db.query(column).distinct().all()

    speeds = get_distinct_values(Game.speed)
    victory_types = get_distinct_values(Game.victory_type)
    version_codes = get_distinct_values(Game.version_code)
    matchups = get_distinct_values(Game.matchup)
    map_sizes = get_distinct_values(Game.map_size)

    stats = {
        'speed': [value for value, in speeds if value],
        'victory_type': [value for value, in victory_types if value],
        'version_code': [value for value, in version_codes if value],
        'matchup': [value for value, in matchups if value],
        'map_size': [value for value, in map_sizes if value]
    }

    current_time = datetime.now().isoformat()

    result = json.dumps(jsonable_encoder({'stats': stats, 'generated_at': current_time}))

    cacher.set('game_option_stats', result)

    return Response(content=result, media_type="application/json")
