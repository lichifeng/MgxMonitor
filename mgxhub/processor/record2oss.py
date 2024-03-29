'''Pack&Upload the record to the OSS storage'''

import os
import tempfile
import zipfile
from datetime import datetime

from mgxhub import cfg, logger
from mgxhub.storage import S3Adapter

from .move2error import move_to_error

_COMMENT_TEMPLATE = '''
Age of Empires II record

Version: {version_code}
Matchup: {matchup}

GUID: {guid}
MD5 : {md5}
(Maybe) Played at: {played_at}

Collected by aocrec.com
Parsed by {parser}
Packed at {current_time}
'''


def save_to_s3(
        recordpath: str,
        gamedata: dict,
        forcereplace: bool = False,
        cleanup: bool = True
) -> str:
    '''Pack&Upload the record to the OSS storage.

    **Failed records will be moved to the error folder.**

    Args:
        recordpath: Path to the record file.
        gamedata: Game metadata.
        forcereplace: Replace the existing file if True.
        cleanup: Clean up the original&packed file if True.

    Returns:
        str: Status message. R2S3_BAD_META, R2S3_EXISTS, R2S3_CONN_ERROR, R2S3_SUCCESS, R2S3_UPLOAD_ERROR
    '''
    # Check necessary keys
    required_keys = ['md5', 'fileext', 'guid']
    if not all(key in gamedata for key in required_keys):
        logger.error(f'Bad gamedata: {recordpath}')
        move_to_error(recordpath, 'badgame')
        return 'R2S3_BAD_META'

    # Establish sqlite connection
    try:
        s3conn = S3Adapter(**cfg.s3)
        desired_file = os.path.join(cfg.get('s3', 'recorddir', fallback=''), f"{gamedata['md5']}.zip")
        if not forcereplace and s3conn.have(desired_file):
            if cleanup and os.path.exists(recordpath):
                os.remove(recordpath)
            return 'R2S3_EXISTS'
    except Exception as e:
        logger.error(f'S3 connection error: {e}')
        move_to_error(recordpath, 's3upload')
        return 'R2S3_CONN_ERROR'

    # Pack the record
    with tempfile.TemporaryFile(suffix='.zip') as temp_file:
        with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as z:
            matchup = gamedata.get('matchup', 'UNKNOWN')
            if 'version' in gamedata and 'code' in gamedata['version']:
                version_code = gamedata['version']['code']
            else:
                version_code = 'UNKNOWN'
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'gameTime' in gamedata and isinstance(gamedata['gameTime'], int):
                played_at = datetime.fromtimestamp(gamedata['gameTime'])\
                    .strftime('%Y-%m-%d %H:%M:%S')
            else:
                played_at = current_time
            packedname = f"{version_code}_{matchup}_{gamedata['md5'][:4]}{gamedata['fileext']}"
            comment = _COMMENT_TEMPLATE.format(
                version_code=version_code,
                matchup=matchup,
                played_at=played_at,
                current_time=current_time,
                data=gamedata,
                guid=gamedata['guid'],
                md5=gamedata['md5'],
                parser=gamedata['parser']
            )
            z.write(recordpath, packedname)
            z.comment = comment.encode('ascii')

        # Upload the record
        try:
            result = s3conn.upload(
                temp_file,
                desired_file,
                metadata={
                    'guid': gamedata['guid'],
                    'md5': gamedata['md5'],
                    'parser': gamedata['parser'],
                    'played': played_at,
                    'version': version_code,
                    'matchup': matchup
                }
            )
            logger.info(f'Uploaded: {result.object_name}')
            if cleanup and os.path.exists(recordpath):
                os.remove(recordpath)
            return 'R2S3_SUCCESS'
        except Exception as e:
            logger.error(f'S3 upload error: {e}')
            move_to_error(recordpath, 's3upload')
            return 'R2S3_UPLOAD_ERROR'


async def async_save_to_s3(
        recordpath: str,
        gamedata: dict,
        forcereplace: bool = False,
        cleanup: bool = True
) -> str:
    '''Async version of save_to_s3.

    **Failed records will be moved to the error folder.**
    '''

    return save_to_s3(recordpath, gamedata, forcereplace, cleanup)
