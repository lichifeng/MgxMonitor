'''Upload a record file to the server'''

from fastapi import Depends, File, Form, UploadFile
from fastapi.security import HTTPBasicCredentials

from mgxhub.auth import WPRestAPI
from mgxhub.handler import FileObjHandler
from webapi import app
from webapi.authdepends import security


@app.post("/game/upload")
async def upload_a_record(
    recfile: UploadFile = File(...),
    lastmod: str = Form(...),
    force_replace: bool = Form(False),
    delete_after: bool = Form(True),
    creds: HTTPBasicCredentials = Depends(security)
):
    '''Upload a record file to the server.

    - **recfile**: The record file to be uploaded.
    - **lastmod**: The last modified time of the record file.

    Optional:
    - **force_replace**: Replace the existing file if it exists. Default is `False`.
    - **delete_after**: Delete the file after processing. Default is `True`.

    Defined in: `webapi/routers/game_upload.py`
    '''

    if force_replace and not WPRestAPI(creds.username, creds.password).need_admin_login(brutal_term=False):
        force_replace = False

    uploaded = FileObjHandler(
        recfile.file, recfile.filename, lastmod,
        {
            "s3_replace": force_replace,
            "delete_after": delete_after
        }
    )

    return uploaded.process()
