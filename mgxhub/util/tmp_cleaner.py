'''Used to handle dangling tmp directories and files created by mgxhub.'''

import os
import shutil

from mgxhub import cfg, logger

# Use global variables for @staticmethod
TMPDIR_PREFIX = cfg.get('system', 'tmpprefix')
TEMPDIR_DIR = cfg.get('system', 'tmpdir')


class TmpCleaner:
    '''Used to handle dangling tmp directories and files created by mgxhub.'''

    def __init__(self):
        # Ensure the tmp directory exists
        os.makedirs(TEMPDIR_DIR, exist_ok=True)

    @staticmethod
    def list_all_tmpdirs() -> list:
        '''List all tmp directories created by mgxhub.'''

        tmpdirs = []
        for tmpdir in os.listdir(TEMPDIR_DIR):
            if tmpdir.startswith(TMPDIR_PREFIX):
                tmpdirs.append(tmpdir)
        return tmpdirs

    @staticmethod
    def purge_all_tmpdirs() -> None:
        '''Purge all stuff in tmp directories'''

        shutil.rmtree(TEMPDIR_DIR)
        os.makedirs(TEMPDIR_DIR)
        logger.warning(f"Purged all tmp directories and files by force: {TEMPDIR_DIR}")
