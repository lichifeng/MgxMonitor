'''Main entry point of the application'''

import os
import io
import asyncio
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
from mgxhub.auth import WPRestAPI, LOGGED_IN_CACHE

Config().load('testconf.ini')
app = FastAPI()
db = DBHandler()
watcher = RecordWatcher()

MAP_DIR = cfg.get('system', 'mapdir')
if MAP_DIR:
    app.mount("/maps", StaticFiles(directory=MAP_DIR), name="maps")


@app.get("/")
async def ping():
    '''Test the server is online or not'''

    return {"time": f"{datetime.now()}", "status": "online"}


@app.get("/system/config/default", response_class=PlainTextResponse)
async def download_default_config() -> str:
    '''Download default configuration file'''

    WPRestAPI().need_admin_login()

    default_conf = DefaultConfig()
    string_io = io.StringIO()
    default_conf.config.write(string_io)
    return string_io.getvalue()


@app.get("/system/config/current", response_class=PlainTextResponse)
async def download_current_config() -> str:
    '''Download current configuration file'''

    WPRestAPI().need_admin_login()

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

    WPRestAPI().need_admin_login()

    lock = RatingLock()
    if lock.rating_running():
        raise HTTPException(status_code=409, detail="Rating calculation process is already running")

    lock.start_calc(batch_size=batch_size, duration_threshold=duration_threshold)
    raise HTTPException(status_code=202, detail="Rating calculation process started")


@app.get("/system/rating/unlock")
async def unlock_rating(force: bool = False) -> dict:
    '''Unlock rating lock or stop rating calculation by force.'''

    WPRestAPI().need_admin_login()

    lock = RatingLock()
    lock.unlock(force)
    if lock.lock_file_exists():
        raise HTTPException(status_code=409, detail="Failed to unlock")

    raise HTTPException(status_code=202, detail="Unlocked")


@app.get("/system/tmpdir/list")
async def list_tmpdirs() -> list:
    '''List all temporary directories created by mgxhub'''

    WPRestAPI().need_admin_login()

    cleaner = TmpCleaner()
    return cleaner.list_all_tmpdirs()


@app.get("/system/tmpdir/purge")
async def purge_tmpdirs() -> dict:
    '''Purge all temporary directories created by mgxhub'''

    WPRestAPI().need_admin_login()
    
    cleaner = TmpCleaner()
    cleaner.purge_all_tmpdirs()

    raise HTTPException(status_code=202, detail="Purge command sent")


@app.get("/game/detail")
async def get_game(guid: str, lang: str = 'en') -> GameDetail | None:
    '''Get details for a game by its GUID.

    - **guid**: GUID of the game.
    - **lang**: Language code. Default is 'en'.
    '''

    details = db.get_game(guid, lang)

    if details:
        return details

    raise HTTPException(status_code=404, detail=f"Game profile [{guid}] not found")


@app.get("/game/random")
async def get_rand_games(threshold: int = 10, limit: int = 50) -> dict:
    '''Fetch random games'''

    return db.fetch_rand_games(threshold, limit)


@app.get("/game/latest")
async def get_latest_games(limit: int = 100) -> dict:
    '''Fetch recently uploaded games

    - **limit**: The number of games to fetch. Default is 100.

    Returned data format:
        [game_guid, version_code, created_time, map_name, matchup, speed, duration, uploader]
    '''

    return db.fetch_latest_games(limit)


@app.post("/game/upload")
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


@app.get("/stats/total")
async def get_index_stats() -> dict:
    '''Get index stats'''

    return db.fetch_index_stats()


@app.get("/player/random")
async def get_rand_players(threshold: int = 10, limit: int = 300) -> dict:
    '''Fetch random players and their game counts'''

    return db.fetch_rand_players(threshold, limit)


@app.get("/player/latest")
async def get_latest_players(limit: int = 20) -> dict:
    '''Fetch latest 20 players and their game counts'''

    return db.fetch_latest_players(limit)


@app.get("/player/friends")
async def get_close_friends(player_hash: str, limit: int = 100) -> dict:
    '''Fetch close friends of a player'''

    return db.fetch_close_friends(player_hash.lower(), limit)


@app.get("/player/profile")
async def get_player_comprehensive(player_hash: str) -> dict:
    '''Fetch comprehensive information of a player'''

    result = await asyncio.gather(
        db.async_fetch_player_totals(player_hash),
        db.async_fetch_player_rating_stats(player_hash),
        db.async_fetch_player_recent_games(player_hash),
        db.async_fetch_close_friends(player_hash)
    )

    return {
        "totals": result[0],
        "ratings": result[1].get('stats', []),
        "recent_games": result[2].get('games', []),
        "close_friends": result[3].get('players', [])
    }


@app.get("/rating/stats")
async def get_rating_meta() -> dict:
    '''Fetch rating metadata'''

    return db.fetch_rating_meta()


@app.get("/rating/table")
async def get_rating_table(
    version_code: str = 'AOC10',
    matchup: str = 'team',
    order: str = 'desc',
    page: int = 0,
    page_size: int = 100
) -> dict:
    '''Fetch rating ladder'''

    return db.fetch_rating(version_code, matchup, order, page, page_size)


@app.get("/rating/player")
async def get_player_rating(
    player_hash: str,
    version_code: str = 'AOC10',
    matchup: str = 'team',
    order: str = 'desc',
    page_size: int = 100
) -> dict:
    '''Fetch rating of a player'''

    return db.fetch_player_rating(player_hash, version_code, matchup, order, page_size)


@app.get("/auth/onlineusers")
async def list_online_users() -> dict:
    '''Check if a user is logged in'''

    WPRestAPI().need_admin_login()
    return LOGGED_IN_CACHE


@app.get("/auth/logoutall")
async def logout_all_users() -> dict:
    '''Logout all users'''

    WPRestAPI().need_admin_login()
    LOGGED_IN_CACHE.clear()
    return {"status": "All users logged out"}
