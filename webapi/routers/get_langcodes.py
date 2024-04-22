'''Get available language codes'''

import os

from mgxhub import cfg
from webapi import app


@app.get("/system/langcodes", tags=['system'])
async def get_langcodes() -> dict[str, list]:
    '''Get available language codes and their names

    Defined in: `webapi/routers/get_langcodes.py`
    '''

    # Scan `translations/en/LC_MESSAGES/` directory for .mo files to get available language codes
    lang_codes = []
    for file in os.listdir(cfg.get('system', 'langdir')):
        if file.endswith('.mo'):
            lang_codes.append(file[:-3])

    return {"lang_codes": lang_codes}
