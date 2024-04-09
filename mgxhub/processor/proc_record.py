'''Process a record file and return the parsed result.'''

import os
import threading

from sqlalchemy.orm import Session

from mgxhub import logger
from mgxhub.parser import parse
from mgxhub.util import run_slow_tasks

from .allowed_types import ACCEPTED_RECORD_TYPES
from .game2sqlite import async_save_game_sqlite
from .map2local import async_save_map
from .map2oss import async_save_map_s3
from .record2oss import async_save_to_s3


def process_record(
        session: Session,
        recpath: str,
        waitio: bool = False,
        opts: str = '',
        s3replace: bool = False,
        cleanup: bool = True
) -> dict:
    '''Process a record file and return the parsed result.

    **Input file should be a raw game record**, not a compressed package or other types.
    Record will be parsed, saved to S3, and inserted into the SQLite database.
    Minimap will be generated and saved to S3/local if available.

    Args:
        recpath (str): The path of the record file to be processed.
        waitio (bool): Whether to wait for the I/O tasks to complete. Like saving to S3 and DB ops.
        opts (str): Options for the processor.
        s3replace (bool): Whether to replace the existing file in S3.
        cleanup (bool): Whether to delete the file after processing.

    Returns:
        dict: The result of the processing.
    '''

    # Check the file existence
    if not os.path.isfile(recpath):
        return {'status': 'error', 'message': 'file not found'}

    # Check the file type
    fileext = recpath.split('.')[-1].lower()
    if fileext not in ACCEPTED_RECORD_TYPES:
        if cleanup:
            os.remove(recpath)
        return {'status': 'error', 'message': 'unsupported file type'}

    # Parse the record
    parsed_result = parse(recpath, opts=opts)
    if parsed_result['status'] in ['error', 'invalid']:
        logger.warning(f'Invalid record: {recpath}')
        if cleanup:
            os.remove(recpath)
        return parsed_result

    # Do upload, db insert, etc.
    tasks = []
    tasks.append(async_save_game_sqlite(session, parsed_result))
    tasks.append(async_save_to_s3(recpath, parsed_result, s3replace, cleanup))
    if 'map' in parsed_result and 'base64' in parsed_result['map']:
        tasks.append(async_save_map(parsed_result['guid'], parsed_result['map']['base64']))
        tasks.append(async_save_map_s3(parsed_result['guid'], parsed_result['map']['base64']))

    slowtasks_thread = threading.Thread(target=run_slow_tasks, args=(tasks,))
    slowtasks_thread.start()
    if waitio:
        slowtasks_thread.join(100)

    # async_save_to_s3() will do the cleanup&error handling
    return parsed_result
