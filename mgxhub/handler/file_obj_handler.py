'''A wrapper of FileHandler for file-like objects.'''

import io
import os
import shutil
import tempfile
from datetime import datetime
from .file_handler import FileHandler
from .tmp_cleaner import TEMPDIR_DIR, TMPDIR_PREFIX


class FileObjHandler(FileHandler):
    """A wrapper of FileHandler for file-like objects."""

    _tmpdir: str | None = None
    _auto_delete: bool = False

    def __init__(self,
                 file: io.StringIO | io.BytesIO | io.TextIOWrapper,
                 filename: str,
                 lastmod: str,
                 handler_opts: dict,
                 auto_delete: bool = False
                 ):
        '''Initialize the handler with a file-like object.

        Args:
            file: The file-like object to be handled.   
            filename: The name of the file.   
            lastmod: The last modified time of the file.   
            handler_opts: Options for the handler.   
            auto_delete: Whether to delete the temporary file after 
                         the handler is deleted. Better do this in
                        FileHandler.
        '''
        self._auto_delete = auto_delete

        # Get valid file last modified time
        try:
            lastmod_obj = datetime.fromisoformat(lastmod)
            if lastmod_obj > datetime.now() or lastmod_obj < datetime(1999, 3, 30):
                raise ValueError
        except ValueError:
            lastmod_obj = datetime.now()

        # Save the file to a temporary location
        self._tmpdir = tempfile.mkdtemp(prefix=TMPDIR_PREFIX, dir=TEMPDIR_DIR)
        recfile = os.path.join(self._tmpdir, filename)
        with open(recfile, 'wb+') as f:
            shutil.copyfileobj(file, f)

        # Change creation time and last modified time of the file
        os.utime(recfile, (lastmod_obj.timestamp(), lastmod_obj.timestamp()))
        print(f"File uploaded, save to: {recfile}")

        super().__init__(recfile, **handler_opts)

    def __del__(self):
        if self._auto_delete and  self._tmpdir and os.path.isdir(self._tmpdir):
            shutil.rmtree(self._tmpdir)
