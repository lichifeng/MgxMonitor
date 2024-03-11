'''Purge all temporary directories created by mgxhub'''

from fastapi.responses import JSONResponse

from mgxhub.handler import TmpCleaner
from webapi.admin_api import admin_api


@admin_api.get("/system/tmpdir/purge")
async def purge_tmpdirs() -> dict:
    '''Purge all temporary directories created by mgxhub
    
    Defined in: `webapi/routers/tmpdir_purge.py`
    '''

    cleaner = TmpCleaner()
    cleaner.purge_all_tmpdirs()

    return JSONResponse(status_code=202, content="Purge command sent")
