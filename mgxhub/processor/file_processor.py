'''Used to process a record file or a compressed package.'''

import io
import os
import random
import shutil
import string
from datetime import datetime

from sqlalchemy.orm import Session

from mgxhub import cfg, logger

from .allowed_types import ACCEPTED_COMPRESSED_TYPES, ACCEPTED_RECORD_TYPES
from .proc_compressed import process_compressed
from .proc_record import process_record

# pylint: disable=R0903


class FileProcessor:
    '''Used to process a record file or a compressed package.

    Args:
        src (str | io.StringIO | io.BytesIO | io.TextIOWrapper): The file path or file-like object to be processed.
        syncproc (bool): Whether to process synchronously.
        s3replace (bool): Whether to replace the existing file in S3.
        cleanup (bool): Whether to delete the file after processing.
        buffermeta (list[str, str] | None): The meta info for the buffer input. Required for buffer input.

    Example:
        ```python
        from mgxhub.processor import FileProcessor

        # Process a record file
        result = FileProcessor('path/to/record.rec').result()

        # Process a file-like object with meta info
        with open('path/to/record.rec', 'rb') as f:
            result = FileProcessor(f, buffermeta=['record.rec', '2021-01-01T12:00:00']).result()
        ```
    '''

    _filepath: str = None
    _syncproc: bool = True
    _s3replace: bool = False
    _cleanup: bool = False
    _tmpdir: str = None
    _output: dict = None
    _session: Session = None

    def __init__(
            self,
            session: Session,
            src: str | io.StringIO | io.BytesIO | io.TextIOWrapper,
            syncproc: bool = True,
            s3replace: bool = False,
            cleanup: bool = False,
            buffermeta: list[str, str] | None = None
    ):
        '''Initialize the FileHandler.'''

        if isinstance(src, str):
            self._filepath = src
        else:
            if not buffermeta:
                raise ValueError('Buffer meta info required for buffer input.')
            self._filepath = self._save_buffer(src, *buffermeta)

        self._session = session
        self._syncproc = syncproc
        self._cleanup = cleanup
        self._s3replace = s3replace

        self._process()

    def _save_buffer(self, src: io.StringIO | io.BytesIO | io.TextIOWrapper, filename: str, lastmod: str) -> str:
        '''Save the file-like object to a temporary location.'''

        # Get valid file last modified time
        try:
            lastmod_obj = datetime.fromisoformat(lastmod)  # This may raise ValueError, too
            if lastmod_obj > datetime.now() or lastmod_obj < datetime(1999, 3, 30):
                raise ValueError
        except ValueError:
            lastmod_obj = datetime.now()

        # Save the file to a temporary location
        self._tmpdir = cfg.get('system', 'tmpdir')
        os.makedirs(self._tmpdir, exist_ok=True)
        recfile = os.path.join(self._tmpdir, filename)
        while os.path.isfile(recfile):
            prefix = ''.join(random.choices(string.ascii_lowercase, k=3))
            recfile = os.path.join(self._tmpdir, f'{prefix}_{filename}')

        with open(recfile, 'wb+') as f:
            shutil.copyfileobj(src, f)

        # Change creation time and last modified time of the file
        os.utime(recfile, (lastmod_obj.timestamp(), lastmod_obj.timestamp()))
        logger.debug(f"Upload buffer saved: {recfile}")

        return recfile

    def _process(self) -> dict:

        if not os.path.isfile(self._filepath):
            self._output = {'status': 'error', 'message': 'file not found'}

        fileext = self._filepath.split('.')[-1].lower()
        if fileext in ACCEPTED_RECORD_TYPES:
            logger.debug(f'Proc(record): {self._filepath}')
            self._output = process_record(self._session, self._filepath, self._syncproc,
                                          '-b', self._s3replace, self._cleanup)
        elif fileext in ACCEPTED_COMPRESSED_TYPES:
            logger.debug(f'Proc(compressed): {self._filepath}')
            self._output = process_compressed(self._filepath, self._cleanup)
        else:
            self._output = {'status': 'invalid', 'message': 'unsupported file type'}

    def result(self) -> dict:
        '''Return the processing result.'''

        return self._output
