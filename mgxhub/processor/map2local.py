'''Save minimap to local file system.'''

import base64
import os
from io import BytesIO

from PIL import Image

from mgxhub import cfg, logger


def save_map(
        basename: str,
        base64src: str,
        dest: str = ''
) -> str:
    '''Save minimap to local file system.

    **Nothing will be done if mapdir is not properly set.** 

    Args:
        basename: Basename of the file. Extension not included.
        base64src: Base64 encoded image.
        dest: Destination folder. Leave empty to use config value.

    Returns:
        str: Status message. MAP_DIR_NOT_SET, MAP_SAVE_SUCCESS, MAP_SAVE_ERROR
    '''

    if cfg.get('system', 'mapdest') != 'local':
        return 'MAP_DIR_NOT_SET'

    # Determine destination folder
    if not dest:
        dest = cfg.get('system', 'mapdir', fallback=None)
    if not dest:
        return 'MAP_DIR_NOT_SET'

    os.makedirs(dest, exist_ok=True)

    # Save the image
    try:
        img = Image.open(BytesIO(base64.b64decode(base64src)))
        img.save(os.path.join(dest, f'{basename}.png'))
        return 'MAP_SAVE_SUCCESS'
    except Exception as e:
        logger.error(f'map2local error: {e}, basename: {basename}')
        return 'MAP_SAVE_ERROR'


async def async_save_map(
        basename: str,
        base64src: str,
        dest: str = ''
) -> str:
    '''Async version of save_map.

    **Nothing will be done if mapdest is not 'local'.** 
    '''

    return save_map(basename, base64src, dest)
