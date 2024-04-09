'''Used to watch the work directory for new files and process them'''

import os
import threading
import time

from mgxhub.config import cfg
from mgxhub.db import db
from mgxhub.logger import logger
from mgxhub.processor import FileProcessor


class RecordWatcher:
    '''Watches the work directory for new files and processes them'''

    def __init__(self):
        '''Initialize the watcher'''

        self.session = db()
        self.work_dir = cfg.get('system', 'uploaddir')
        os.makedirs(self.work_dir, exist_ok=True)

        if self.work_dir and os.path.isdir(self.work_dir):
            self.thread = threading.Thread(target=self._watch, daemon=True)
            self.thread.start()
            logger.info(f"[Watcher] Monitoring directory: {self.work_dir}")

    def _watch(self):
        '''Watch the work directory for new files and process them'''

        while True:
            self._scan(self.work_dir)
            time.sleep(1)

    def _scan(self, dirpath: str):
        for root, dirs, files in os.walk(dirpath):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    file_processor = FileProcessor(self.session, file_path, syncproc=True,
                                                   s3replace=False, cleanup=True)
                except Exception as e:
                    logger.error(f"[Watcher] Error [{file_path}]: {e}")
                    # This exception may due to unfinished file writing, so we wait for a while
                    time.sleep(3)
                    return
                logger.debug(
                    f"[Watcher] {file_path}: {file_processor.result().get('status', 'unknown')}")
                if os.path.isfile(file_path):
                    os.remove(file_path)
            for inner_dir in dirs:
                inner_path = os.path.join(root, inner_dir)
                self._scan(inner_path)
                if os.path.isdir(inner_path):
                    try:
                        os.rmdir(inner_path)
                    except OSError:
                        logger.warning(f'Try removing non-empty dir: {inner_dir}')
