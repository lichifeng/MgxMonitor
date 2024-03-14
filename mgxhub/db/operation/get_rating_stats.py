'''Get rating statistics of different versions'''

from sqlalchemy import desc, func

from mgxhub import db
from mgxhub.model.orm import Rating

# pylint: disable=not-callable


def get_rating_stats() -> list:
    '''Get rating statistics of different versions

    Used in ratings page to show the number of ratings for each version.

    Defined in: `mgxhub/db/operation/get_rating_stats.py`
    '''

    count = func.count(Rating.version_code).label('count')

    result = db().query(
        Rating.version_code,
        count
    ).group_by(
        Rating.version_code
    ).order_by(
        desc(count)
    ).all()

    return [tuple(row) for row in result]
