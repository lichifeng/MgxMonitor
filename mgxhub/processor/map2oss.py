'''Save minimap to s3 storage'''

import base64
import os
from io import BytesIO

from PIL import Image

from mgxhub import cfg, logger
from mgxhub.storage import S3Adapter


def save_map_s3(
        basename: str,
        base64src: str,
        dest: str = ''
) -> str:
    '''Save minimap to s3 storage.

    Args:
        basename: Basename of the file. Extension not included.
        base64src: Base64 encoded image.
        dest: Destination folder. Leave empty to use config value.

    Returns:
        str: Status message. MAP_OSS_ERROR, MAP_UPLOAD_SUCCESS, MAP_UPLOAD_ERROR
    '''

    # Determine destination folder
    if not dest:
        dest = cfg.get('system', 'mapdirS3', fallback='')

    # Eastablish connection to s3
    try:
        s3conn = S3Adapter(**cfg.s3)
    except Exception as e:
        logger.error(f'[MAP] S3 connection failed: {e}')
        return 'MAP_OSS_ERROR'

    # Upload the image
    try:
        img = Image.open(BytesIO(base64.b64decode(base64src)))
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        result = s3conn.upload(
            buf, os.path.join(dest, f'{basename}.png'),
            content_type='image/png')
        logger.debug(f'Map uploaded: {result.object_name}')
        return 'MAP_UPLOAD_SUCCESS'
    except Exception as e:
        logger.error(f'map2oss error: {e}, basename: {basename}')
        return 'MAP_UPLOAD_ERROR'


async def async_save_map_s3(
        basename: str,
        base64src: str,
        dest: str = ''
) -> str:
    '''Async version of save_map_s3.'''

    return save_map_s3(basename, base64src, dest)
