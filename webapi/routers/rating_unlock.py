'''Unlock rating lock or stop rating calculation by force'''

from fastapi.responses import JSONResponse

from mgxhub.rating import RatingLock
from webapi.admin_api import admin_api


@admin_api.get("/rating/unlock", tags=['rating'])
async def unlock_rating(force: bool = False) -> dict:
    '''Unlock rating lock or stop rating calculation by force

    Defined in: `webapi/routers/rating_unlock.py`
    '''

    lock = RatingLock()
    lock.unlock(force)
    if lock.lock_file_exists():
        return JSONResponse(status_code=409, content="Failed to unlock")

    return JSONResponse(status_code=202, content="Unlocked")
