'''Used to handle dangling tmp directories and files created by mgxhub.'''

import os
import shutil

TMPDIR_PREFIX = 'mgxhubtmp_'
# TMPDIR_DIR is tmp directory of ../../tmp relative to this file
# aka tmp/ under project root
TEMPDIR_DIR = os.path.join(os.path.dirname(__file__), '../../__tmp')

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
        '''Purge all tmp directories created by mgxhub.'''

        for tmpdir in os.listdir(TEMPDIR_DIR):
            if tmpdir.startswith(TMPDIR_PREFIX):
                shutil.rmtree(os.path.join(TEMPDIR_DIR, tmpdir))