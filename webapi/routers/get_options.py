'''Get option values like 1v1, 2v2, 3v3, AOC10, AOC10C, etc.'''

from sqlalchemy import desc, func

from mgxhub import db
from mgxhub.model.orm import Game
from webapi import app

# pylint: disable=not-callable


@app.get("/optionvalues")
async def get_option_values() -> dict:

    def get_counts(column):
        return db().query(
            column, func.count(column).label('count')
        ).group_by(
            column
        ).order_by(desc('count')).all()

    matchups = get_counts(Game.matchup)
    versions = get_counts(Game.version_code)
    mapsizes = get_counts(Game.map_size)
    speeds = get_counts(Game.speed)

    result = {
        'matchups': dict(matchups),
        'versions': dict(versions),
        'mapsizes': dict(mapsizes),
        'speeds': dict(speeds)
    }

    return result
