'''Get option values like 1v1, 2v2, 3v3, AOC10, AOC10C, etc.'''

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from mgxhub import db
from mgxhub.model.orm import Game
from webapi import app

# pylint: disable=not-callable


@app.get("/optionvalues")
async def get_option_values() -> dict:
    '''Get option values like 1v1, 2v2, 3v3, AOC10, AOC10C, etc.

    Returns:
        A dictionary containing the option values.

    Defined in: `mgxhub/db/operation/get_option_values.py`
    '''

    def get_counts(session: Session, column):
        return session.query(
            column, func.count(column).label('count')
        ).group_by(
            column
        ).order_by(desc('count')).all()

    session = db()
    matchups = get_counts(session, Game.matchup)
    versions = get_counts(session, Game.version_code)
    mapsizes = get_counts(session, Game.map_size)
    speeds = get_counts(session, Game.speed)

    result = {
        'matchups': dict(matchups),
        'versions': dict(versions),
        'mapsizes': dict(mapsizes),
        'speeds': dict(speeds)
    }

    return result
