'''Reparse a record file to update its information'''

from datetime import datetime

from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from mgxhub import cfg, db
from mgxhub.model.orm import File
from mgxhub.processor import FileProcessor
from mgxhub.storage import S3Adapter
from webapi.admin_api import admin_api


def _reparse(session: Session, guid: str) -> None:
    oss = S3Adapter(**cfg.s3)
    file_records = session.query(File.md5).filter(File.game_guid == guid).all()
    file_md5s = [f[0] for f in file_records]
    for filemd5 in file_md5s:
        downloaded = oss.download(f"/records/{filemd5}.zip")
        if downloaded:
            FileProcessor(
                session,
                downloaded,
                syncproc=True,
                s3replace=False,
                cleanup=True,
                buffermeta=[f"{filemd5}.zip", datetime.now().isoformat()]
            )


@admin_api.get("/game/reparse")
async def reparse_a_record(background_tasks: BackgroundTasks, guid: str) -> dict:
    '''Reparse a record file to update its information.

    Used when parser is updated.

    - **guid**: The GUID of the record file.

    Defined in: `webapi/routers/game_reparse.py`
    '''

    session = db()
    background_tasks.add_task(_reparse, session, guid)

    return JSONResponse(status_code=202, content={"detail": f"Reparse command sent for [{guid}]"})
