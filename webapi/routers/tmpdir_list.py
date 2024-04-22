'''List all temporary directories created by mgxhub'''

from mgxhub.util import TmpCleaner
from webapi.admin_api import admin_api


@admin_api.get("/system/tmpdir/list", tags=['system'])
async def list_tmpdirs() -> list:
    '''List all temporary directories created by mgxhub

    Defined in: `webapi/routers/tmpdir_list.py`
    '''

    cleaner = TmpCleaner()
    return cleaner.list_all_tmpdirs()
