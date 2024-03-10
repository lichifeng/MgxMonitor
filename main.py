'''Main entry point of the application'''

import os
import io
import asyncio
from datetime import datetime
from fastapi import FastAPI, Form, UploadFile, File, BackgroundTasks, Depends, APIRouter, Body, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from mgxhub.model.webapi import GameDetail
from mgxhub.handler import DBHandler, FileObjHandler, TmpCleaner
from mgxhub.rating import RatingLock
from mgxhub.watcher import RecordWatcher
from mgxhub.config import cfg, DefaultConfig
from mgxhub.auth import WPRestAPI, LOGGED_IN_CACHE
from mgxhub.storage import S3Adapter
from mgxhub.util.sqlite3 import sqlite3backup
from mgxhub.auth.authrouter import need_admin_login, security
from mgxhub.model.searchcriteria import SearchCriteria

app = FastAPI()
admin_auth_router = APIRouter(dependencies=[Depends(need_admin_login)])

db = DBHandler()
watcher = RecordWatcher()
security = HTTPBasic()

MAP_DIR = cfg.get('system', 'mapdir')
if MAP_DIR:
    app.mount("/maps", StaticFiles(directory=MAP_DIR), name="maps")


@app.get("/")
async def ping():
    '''Test the server is online or not'''

    return {"time": f"{datetime.now()}", "status": "online"}


@admin_auth_router.get("/system/config/default", response_class=PlainTextResponse)
async def download_default_config() -> str:
    '''Download default configuration file'''

    default_conf = DefaultConfig()
    string_io = io.StringIO()
    default_conf.config.write(string_io)
    return string_io.getvalue()


@admin_auth_router.get("/system/config/current", response_class=PlainTextResponse)
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


@admin_auth_router.get("/system/rating/start")
async def start_rating_calc(
    batch_size: str = cfg.get('rating', 'batchsize'),
    duration_threshold: str = cfg.get('rating', 'durationthreshold'),
    shcedule: bool = False
) -> dict:
    '''Start the rating calculation process.'''

    lock = RatingLock()
    if lock.rating_running():
        if shcedule:
            lock.schedule()
            return JSONResponse(status_code=202, content="Rating calculation process is already running, scheduled the next calculation")
        return JSONResponse(status_code=409, content="Rating calculation process is already running")

    lock.start_calc(batch_size=batch_size, duration_threshold=duration_threshold, schedule=shcedule)
    return JSONResponse(status_code=202, content="Rating calculation process started")


@admin_auth_router.get("/system/rating/unlock")
async def unlock_rating(force: bool = False) -> dict:
    '''Unlock rating lock or stop rating calculation by force.'''

    lock = RatingLock()
    lock.unlock(force)
    if lock.lock_file_exists():
        return JSONResponse(status_code=409, content="Failed to unlock")

    return JSONResponse(status_code=202, content="Unlocked")


@admin_auth_router.get("/system/tmpdir/list")
async def list_tmpdirs() -> list:
    '''List all temporary directories created by mgxhub'''

    cleaner = TmpCleaner()
    return cleaner.list_all_tmpdirs()


@admin_auth_router.get("/system/tmpdir/purge")
async def purge_tmpdirs() -> dict:
    '''Purge all temporary directories created by mgxhub'''

    cleaner = TmpCleaner()
    cleaner.purge_all_tmpdirs()

    return JSONResponse(status_code=202, content="Purge command sent")


@admin_auth_router.get("/system/backup/sqlite")
async def backup_sqlite(background_tasks: BackgroundTasks) -> dict:
    '''Backup SQLite3 database'''

    if os.path.exists(cfg.get('database', 'sqlite')):
        background_tasks.add_task(sqlite3backup)
        return JSONResponse(status_code=202, content="Backup command sent")
    return JSONResponse(status_code=404, content="No valid SQLite3 database found")


@app.get("/game/detail")
async def get_game(guid: str, lang: str = 'en') -> GameDetail | None:
    '''Get details for a game by its GUID.

    - **guid**: GUID of the game.
    - **lang**: Language code. Default is 'en'.
    '''

    details = db.get_game(guid, lang)

    if details:
        return details

    return JSONResponse(status_code=404, content=f"Game profile [{guid}] not found")


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
    recfile: UploadFile = File(...),
    lastmod: str = Form(...),
    force_replace: bool = Form(False),
    delete_after: bool = Form(True),
    creds: HTTPBasicCredentials = Depends(security)
):
    '''Upload a record file to the server.

    - **recfile**: The record file to be uploaded.
    - **lastmod**: The last modified time of the record file.
    '''

    if force_replace and not WPRestAPI(creds.username, creds.password).need_admin_login(brutal_term=False):
        force_replace = False

    uploaded = FileObjHandler(
        recfile.file, recfile.filename, lastmod,
        {
            "s3_replace": force_replace,
            "delete_after": delete_after,
            "db_handler": db
        }
    )

    return uploaded.process()


@admin_auth_router.get("/game/reparse")
async def reparse_a_record(background_tasks: BackgroundTasks, guid: str) -> dict:
    '''Reparse a record file to update its information.

    Used when parser is updated.

    - **guid**: The GUID of the record file.
    '''

    def _reparse(guid):
        oss = S3Adapter(**cfg.s3)
        for fmd5 in db.get_record_files(guid):
            downloaded = oss.download(f"/records/{fmd5}.zip")
            if downloaded:
                reparsed = FileObjHandler(
                    downloaded, f"{fmd5}.mgx", datetime.now().isoformat(),
                    {
                        "s3_replace": False,
                        "delete_after": True,
                        "db_handler": db
                    }
                )
                reparsed.process()

    background_tasks.add_task(_reparse, guid)
    return JSONResponse(status_code=202, content={"detail": f"Reparse command sent for [{guid}]"})


@app.post("/game/search")
async def search_games(criteria: SearchCriteria = Body(...)) -> dict:
    '''Search games by query string'''

    if not criteria:
        raise HTTPException(status_code=400, detail="Invalid search criteria")

    return db.search_games(criteria)


@app.get("/game/optionstats")
async def get_game_option_stats() -> dict:
    '''Get game option stats'''

    return db.stat_unique_game_options()

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


@app.get("/player/searchname")
async def search_player_by_name(
    player_name: str,
    stype: str = 'std',
    orderby: str = 'nagd',
    page: int = 0,
    page_size: int = 100
) -> dict:
    '''Search player by name'''

    return db.search_players_by_name(player_name, stype, orderby, page, page_size)


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


@admin_auth_router.get("/auth/onlineusers")
async def list_online_users() -> dict:
    '''Check if a user is logged in'''

    return LOGGED_IN_CACHE


@admin_auth_router.get("/auth/logoutall")
async def logout_all_users() -> dict:
    '''Logout all users'''

    LOGGED_IN_CACHE.clear()
    return {"status": "All users logged out"}

app.include_router(admin_auth_router)
