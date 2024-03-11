'''Main entry point of the application'''


from mgxhub.handler import DBHandler
from mgxhub.watcher import RecordWatcher
from webapi import app
from webapi.admin_api import admin_api
# pylint: disable=unused-import
from webapi.routers import (auth_logoutall, auth_onlineusers, backup_sqlite,
                            download_current_config, download_default_config,
                            game_detail, game_latest, game_optionstats,
                            game_random, game_reparse, game_search,
                            game_upload, get_langcodes, map_static, ping,
                            player_friends, player_latest, player_profile,
                            player_random, player_searchname, rating_start,
                            rating_status, rating_unlock, stats_total,
                            tmpdir_list, tmpdir_purge)

db = DBHandler()
watcher = RecordWatcher()


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


app.include_router(admin_api)
