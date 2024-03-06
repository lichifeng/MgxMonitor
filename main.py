'''Main entry point of the application'''

import os
import io
from datetime import datetime
from typing import Annotated
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from mgxhub.model.webapi import GameDetail
from mgxhub.handler import DBHandler, FileObjHandler, TmpCleaner
from mgxhub.rating import RatingLock
from mgxhub.watcher import RecordWatcher
from mgxhub.config import cfg, Config, DefaultConfig

Config().load('testconf.ini')
app = FastAPI()
db = DBHandler()
watcher = RecordWatcher()

@app.get("/")
async def ping():
    '''Test the server is online or not'''

    return {"time": f"{datetime.now()}", "status": "online"}


@app.get("/system/config/default", response_class=PlainTextResponse)
async def download_default_config() -> str:
    '''Download default configuration file'''

    default_conf = DefaultConfig()
    string_io = io.StringIO()
    default_conf.config.write(string_io)
    return string_io.getvalue()


@app.get("/system/config/current", response_class=PlainTextResponse)
async def download_current_config() -> str:
    '''Download current configuration file'''

    string_io = io.StringIO()
    cfg.write(string_io)
    return string_io.getvalue()


@app.get("/system/langcodes")
async def get_langcodes() -> dict[str, list]:
    '''Get available language codes and their names'''

    # Scan `translations/` directory for .po files to get available language codes
    lang_codes = []
    for file in os.listdir(cfg.get('system', 'langdir')):
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
async def start_rating_calc(
    batch_size: str = cfg.get('rating', 'batchsize'), 
    duration_threshold: str = cfg.get('rating', 'durationthreshold')
) -> dict:
    '''Start the rating calculation process.'''

    lock = RatingLock()
    if lock.rating_running():
        raise HTTPException(status_code=409, detail="Rating calculation process is already running")

    lock.start_calc(batch_size=batch_size, duration_threshold=duration_threshold)
    raise HTTPException(status_code=202, detail="Rating calculation process started")


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
            "s3_replace": True,
            "delete_after": True,
            "db_handler": db
        }
    )

    # TODO 到底返回什么样的值？要不要返回地图？
    return uploaded.process()


@app.get("/fetch/indexstats")
async def get_index_stats() -> dict:
    '''Get index stats'''

    return db.fetch_index_stats()


@app.get("/fetch/randplayers")
async def get_rand_players(threshold: int = 10, limit: int = 300) -> dict:
    '''Fetch random players and their game counts'''

    return db.fetch_rand_players(threshold, limit)


@app.get("/fetch/randgames")
async def get_rand_games(threshold: int = 10, limit: int = 50) -> dict:
    '''Fetch random games'''

    return db.fetch_rand_games(threshold, limit)


@app.get("/fetch/latestplayers")
async def get_latest_players(limit: int = 20) -> dict:
    '''Fetch latest 20 players and their game counts'''

    return db.fetch_latest_players(limit)


@app.get("/fetch/closefriends")
async def get_close_friends(player_hash: str, limit: int = 100) -> dict:
    '''Fetch close friends of a player'''

    return db.fetch_close_friends(player_hash.lower(), limit)


@app.get("/fetch/latestgames")
async def get_latest_games(limit: int = 100) -> dict:
    '''Fetch recently uploaded games
    
    - **limit**: The number of games to fetch. Default is 100.

    Returned data format:
        [game_guid, version_code, created_time, map_name, matchup, speed, duration, uploader]
    '''

    return db.fetch_latest_games(limit)


@app.get("/fetch/ratingmeta")
async def get_rating_meta() -> dict:
    '''Fetch rating metadata'''

    return db.fetch_rating_meta()


@app.get("/fetch/rating")
async def get_rating_table(
    version_code: str = 'AOC10', 
    matchup: str = 'team', 
    order: str = 'desc',
    offset: int = 0,
    limit: int = 100
) -> dict:
    '''Fetch rating ladder'''

    return db.fetch_rating(version_code, matchup, order, offset, limit)


MAP_DIR = cfg.get('system', 'mapdir')
if MAP_DIR:
    app.mount("/maps", StaticFiles(directory=MAP_DIR), name="maps")
