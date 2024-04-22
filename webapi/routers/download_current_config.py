'''Download current configuration file'''

import io

from fastapi.responses import PlainTextResponse

from mgxhub import cfg
from webapi.admin_api import admin_api


@admin_api.get("/system/config/current", response_class=PlainTextResponse, tags=['system'])
async def download_current_config() -> str:
    '''Download current configuration file

    Defined in: `webapi/routers/download_current_config.py`
    '''

    string_io = io.StringIO()
    cfg.write(string_io)
    return string_io.getvalue()
