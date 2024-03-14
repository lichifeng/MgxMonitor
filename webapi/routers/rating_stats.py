'''Get rating statistics of different versions'''

from datetime import datetime

from fastapi import BackgroundTasks

from mgxhub.db.operation import get_rating_stats
from webapi import app

STATS_CACHE = None


@app.get("/rating/stats")
async def get_rating_meta(background_tasks: BackgroundTasks) -> dict:
    '''Get rating statistics of different versions.

    Used in ratings page to show the number of rating records for each version.

    Defined in: `webapi/routers/rating_stats.py`
    '''

    global STATS_CACHE  # pylint: disable=global-statement

    current_time = datetime.now().isoformat()

    if STATS_CACHE:
        background_tasks.add_task(get_rating_stats)
        return {
            'stats': STATS_CACHE,
            'generated_at': current_time

        }

    STATS_CACHE = get_rating_stats()

    return {'stats': STATS_CACHE, 'generated_at': current_time}
