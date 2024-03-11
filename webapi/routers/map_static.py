'''Provide router for static map files'''

from fastapi.staticfiles import StaticFiles

from mgxhub import cfg
from webapi import app

MAP_DIR = cfg.get('system', 'mapdir')
if MAP_DIR:
    app.mount("/maps", StaticFiles(directory=MAP_DIR), name="maps")
