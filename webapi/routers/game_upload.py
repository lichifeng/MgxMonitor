'''Upload a record file to the server'''

from datetime import datetime

from fastapi import Depends, File, Form, UploadFile
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session

from mgxhub import logger
from mgxhub.auth import WPRestAPI
from mgxhub.db import db_dep
from mgxhub.processor import FileProcessor
from webapi import app
from webapi.authdepends import security


@app.post("/game/upload", tags=['game'])
async def upload_a_record(
    recfile: UploadFile = File(...),
    lastmod: str = Form(''),
    s3replace: bool = Form(False),
    cleanup: bool = Form(True),
    creds: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(db_dep)
):
    '''Upload a record file to the server.

    See https://github.com/lichifeng/MgxParser#about-status for the status explanation.

    - **recfile**: The record file to be uploaded.

    Optional:
    - **lastmod**: The last modified time of the record file. If not provided, the current time will be used.
    - **force_replace**: Replace the existing file if it exists. Default is `False`.
    - **delete_after**: Delete the file after processing. Default is `True`.

    Defined in: `webapi/routers/game_upload.py`
    '''

    if s3replace and not WPRestAPI(creds.username, creds.password).need_admin_login(brutal_term=False):
        s3replace = False

    if not lastmod:
        lastmod = datetime.now().isoformat()
    else:
        try:
            lastmod = datetime.fromtimestamp(float(lastmod)).isoformat()
        except Exception as e:
            logger.warning(f'Invalid lastmod: {e}')
            lastmod = datetime.now().isoformat()

    processed = FileProcessor(
        db,
        recfile.file,
        syncproc=False,
        s3replace=s3replace,
        cleanup=cleanup,
        buffermeta=[recfile.filename, lastmod]
    )

    return processed.result()
