'''Upload a record file to the server'''

from datetime import datetime

from fastapi import Depends, File, Form, UploadFile
from fastapi.security import HTTPBasicCredentials

from mgxhub.auth import WPRestAPI
from mgxhub.processor import FileProcessor
from webapi import app
from webapi.authdepends import security


@app.post("/game/upload")
async def upload_a_record(
    recfile: UploadFile = File(...),
    lastmod: str = Form(''),
    s3replace: bool = Form(False),
    cleanup: bool = Form(True),
    creds: HTTPBasicCredentials = Depends(security)
):
    '''Upload a record file to the server.

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

    processed = FileProcessor(
        recfile.file,
        syncproc=False,
        s3replace=s3replace,
        cleanup=cleanup,
        buffermeta=[recfile.filename, lastmod]
    )

    return processed.result()
