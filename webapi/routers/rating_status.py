'''Get status of the rating calculation process'''

from mgxhub.rating import RatingLock
from webapi import app


@app.get("/rating/status", tags=['rating'])
async def get_rating_status() -> dict:
    '''Get status of the rating calculation process

    Defined in: `webapi/routers/rating_status.py`
    '''

    lock = RatingLock()

    return {
        "running": lock.rating_running(),
        "pid": lock.pid,
        "started": lock.started_time,
        "elapsed": lock.time_elapsed
    }
