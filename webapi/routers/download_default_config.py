'''Download default configuration file'''

import io

from fastapi.responses import PlainTextResponse

from mgxhub.config import DefaultConfig
from webapi.admin_api import admin_api


@admin_api.get("/system/config/default", response_class=PlainTextResponse)
async def download_default_config() -> str:
    '''Download default configuration file
    
    Defined in: `webapi/routers/download_default_config.py`
    '''

    default_conf = DefaultConfig()
    string_io = io.StringIO()
    default_conf.config.write(string_io)
    return string_io.getvalue()