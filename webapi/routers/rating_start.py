'''Start the rating calculation process'''

from fastapi.responses import JSONResponse

from mgxhub import cfg
from mgxhub.rating import RatingLock
from webapi.admin_api import admin_api


@admin_api.get("/system/rating/start")
async def start_rating_calc(
    batch_size: str | None = None,
    duration_threshold: str | None = None,
    shcedule: bool = False
) -> dict:
    '''Start the rating calculation process
    
    Defined in: `webapi/routers/rating_start.py`
    '''

    if batch_size is None:
        batch_size = cfg.get('rating', 'batchsize')
    if duration_threshold is None:
        duration_threshold = cfg.get('rating', 'durationthreshold')

    lock = RatingLock()
    if lock.rating_running():
        if shcedule:
            lock.schedule()
            return JSONResponse(status_code=202, content="Rating calculation process is already running, scheduled the next calculation")
        return JSONResponse(status_code=409, content="Rating calculation process is already running")

    lock.start_calc(batch_size=batch_size, duration_threshold=duration_threshold, schedule=shcedule)
    return JSONResponse(status_code=202, content="Rating calculation process started")
