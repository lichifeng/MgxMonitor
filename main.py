'''Main entry point of the application'''

from mgxhub.watcher import RecordWatcher
from webapi import app
from webapi.admin_api import admin_api
# pylint: disable=unused-import
from webapi.routers import (auth_logoutall, auth_onlineusers, backup_sqlite,
                            download_current_config, download_default_config,
                            game_delete, game_detail, game_latest,
                            game_optionstats, game_random, game_reparse,
                            game_search, game_upload, game_visibility,
                            get_langcodes, get_options, map_static, ping,
                            player_active, player_friends, player_latest,
                            player_profile, player_random, player_recent_game,
                            player_searchname, rating_player_page,
                            rating_searchname, rating_start, rating_stats,
                            rating_status, rating_table, rating_unlock,
                            stats_total, tmpdir_list, tmpdir_purge)

# Start monitoring the upload directory
watcher = RecordWatcher()

app.include_router(admin_api)
