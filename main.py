'''Main entry point of the application'''

import os
from datetime import datetime
from typing import Annotated
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from mgxhub.model.webapi import GameDetail
from mgxhub.handler import DBHandler, FileObjHandler, TmpCleaner
from mgxhub.rating import RatingLock
from mgxhub.watcher import RecordWatcher

s3_test = [
        "play.min.io",
        "Q3AM3UQ867SPQQA43P2F",
        "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
        "us-east-1",
        "aocrec-test-bucket"
    ]

app = FastAPI()
db = DBHandler()
watcher = RecordWatcher(s3_creds=s3_test, db=db)


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


@app.get("/system/tmpdir/list")
async def list_tmpdirs() -> list:
    '''List all temporary directories created by mgxhub'''

    cleaner = TmpCleaner()
    return cleaner.list_all_tmpdirs()


@app.get("/system/tmpdir/purge")
async def purge_tmpdirs() -> dict:
    '''Purge all temporary directories created by mgxhub'''

    cleaner = TmpCleaner()
    cleaner.purge_all_tmpdirs()

    raise HTTPException(status_code=202, detail="Purge command sent")


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


@app.post("/upload")
async def upload_a_record(
    recfile: Annotated[UploadFile, File()],
    lastmod: Annotated[str, Form()],
):
    '''Upload a record file to the server.

    - **recfile**: The record file to be uploaded.
    - **lastmod**: The last modified time of the record file.
    '''

    uploaded = FileObjHandler(
        recfile.file, recfile.filename, lastmod,
        {
            "s3_creds": s3_test,
            "s3_replace": True,
            "delete_after": True,
            "db_handler": db
        }
    )

    # TODO 到底返回什么样的值？要不要返回地图？
    return uploaded.process()


MAP_DIR = os.getenv("MAP_DIR")
if MAP_DIR:
    app.mount("/maps", StaticFiles(directory=MAP_DIR), name="maps")
