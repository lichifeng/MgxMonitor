'''Move unprocessed files to error folder'''

import os
import random
import shutil
import string

from mgxhub import cfg


def move_to_error(
        src: str,
        dest: str = '',
        copy: bool = False,
        errordir: str | None = None
) -> str:
    '''Move unprocessed files to error folder

    Args:
        src: Source file
        dest: Destination folder. Subfolder name under error_folder. Default is None.
        copy: Copy files instead of moving. Meta data is also copied.
        error_folder: Error folder

    Returns:
        str: Path after moving
    '''

    # Check and create destination folder
    if not errordir:
        errordir = cfg.get('system', 'errordir')
    destdir = os.path.join(errordir, dest)
    os.makedirs(destdir, exist_ok=True)

    # Determine destination file name
    filename = os.path.basename(src)
    destname = filename
    destexist = os.path.isfile(os.path.join(destdir, destname))
    while destexist:
        prefix = ''.join(random.choices(string.ascii_lowercase, k=3))
        destname = f'{prefix}_{filename}'
        destexist = os.path.isfile(os.path.join(destdir, destname))
    destpath = os.path.join(destdir, destname)

    # Do the action
    if copy:
        shutil.copy2(src, destpath)
    else:
        shutil.move(src, destpath)

    return destpath
