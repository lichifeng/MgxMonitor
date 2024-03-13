'''Backup SQLite3 database'''

import os

from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse

from mgxhub import cfg
from mgxhub.util.backup import sqlite3backup
from webapi.admin_api import admin_api


@admin_api.get("/system/backup/sqlite")
async def backup_sqlite(background_tasks: BackgroundTasks) -> dict:
    '''Backup SQLite3 database

    Defined in: `webapi/routers/backup_sqlite.py`
    '''

    if os.path.exists(cfg.get('database', 'sqlite')):
        background_tasks.add_task(sqlite3backup)
        return JSONResponse(status_code=202, content="Backup command sent")
    return JSONResponse(status_code=404, content="No valid SQLite3 database found")
