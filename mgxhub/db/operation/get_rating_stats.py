'''Get rating statistics of different versions'''

from sqlalchemy import text

from mgxhub import db


def get_rating_stats() -> list:
    '''Get rating statistics of different versions

    Used in ratings page to show the number of ratings for each version.

    Defined in: `mgxhub/db/operation/get_rating_stats.py`
    '''

    query = text("""
            SELECT version_code, COUNT(*) as count
            FROM ratings
            GROUP BY version_code
            ORDER BY count DESC;
        """)

    result = db().execute(query)
    return [tuple(row) for row in result.fetchall()]


async def async_get_rating_stats() -> list:
    '''Async version of fetch_rating_meta()'''

    return get_rating_stats()
