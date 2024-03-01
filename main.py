'''Main entry point of the application'''

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from mgxhub.model.webapi import GameDetail
from mgxhub.handler import DBHandler
from mgxhub.rating import RatingLock


app = FastAPI()
db = DBHandler()


@app.get("/")
async def ping():
    '''Test the server is online or not'''

    return {"time": f"{datetime.now()}", "status": "online"}


@app.get("/system/langcodes")
async def get_langcodes() -> dict[str, list]:
    '''Get available language codes and their names'''

    # Scan `translations/` directory for .po files to get available language codes
    lang_codes = []
    for file in os.listdir('translations/LC_MESSAGES/'):
        if file.endswith('.mo'):
            lang_codes.append(file[:-3])

    return {"lang_codes": lang_codes}


@app.get("/system/rating/status")
async def get_rating_status() -> dict:
    '''Get status of the rating calculation process.'''

    lock = RatingLock()
    return {
        "running": lock.rating_running(),
        "pid": lock.pid,
        "started": lock.started_time,
        "elapsed": lock.time_elapsed
    }


@app.get("/system/rating/start")
async def start_rating_calc() -> dict:
    '''Start the rating calculation process.'''

    lock = RatingLock()
    if lock.rating_running():
        raise HTTPException(
            status_code=409, detail="Rating calculation process is already running")

    lock.start_calc()
    raise HTTPException(
        status_code=202, detail="Rating calculation process started")


@app.get("/system/rating/unlock")
async def unlock_rating(force: bool = False) -> dict:
    '''Unlock rating lock or stop rating calculation by force.'''

    lock = RatingLock()
    lock.unlock(force)
    if lock.lock_file_exists():
        raise HTTPException(status_code=409, detail="Failed to unlock")

    raise HTTPException(status_code=202, detail="Unlocked")


@app.get("/game/{game_guid}")
async def get_game(game_guid: str, lang: str = 'en') -> GameDetail | None:
    '''Get details for a game by its GUID.

    - **game_guid**: GUID of the game.
    - **lang**: Language code. Default is 'en'.
    '''

    details = db.get_game(game_guid, lang)

    if details:
        return details

    raise HTTPException(
        status_code=404, detail=f"Game profile [{game_guid}] not found")
