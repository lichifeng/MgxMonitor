'''Get option for speed, victory type, version code, matchup, map size, etc.'''

from datetime import datetime

from fastapi import Depends
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.model.orm import Game
from webapi import app


@app.get("/game/optionstats", tags=['game'])
async def get_game_option_stats(db: Session = Depends(db_dep)) -> dict:
    '''Get option for speed, victory type, version code, matchup, map size, etc.

    Returns:
        A dictionary containing the option stats.

    Defined in: `mgxhub/db/operation/game_optionstats.py`
    '''

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

    return {'stats': stats, 'generated_at': current_time}
