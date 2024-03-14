'''Used to watch the work directory for new files and process them'''

import os
import threading
import time

from mgxhub.config import cfg
from mgxhub.logger import logger
from mgxhub.processor import FileProcessor


class RecordWatcher:
    '''Watches the work directory for new files and processes them'''

    def __init__(self):
        self.work_dir = cfg.get('system', 'uploaddir')
        os.makedirs(self.work_dir, exist_ok=True)

        if self.work_dir and os.path.isdir(self.work_dir):
            self.thread = threading.Thread(target=self._watch, daemon=True)
            self.thread.start()
            logger.info(f"[Watcher] Monitoring directory: {self.work_dir}")

    def _watch(self):
        '''Watch the work directory for new files and process them'''

        while True:
            for filename in os.listdir(self.work_dir):
                file_path = os.path.join(self.work_dir, filename)
                logger.info(f"[Watcher] Found file: {file_path}")
                file_processor = FileProcessor(file_path, delete_after=True)
                try:
                    file_processor.process()
                    time.sleep(0.05)
                except Exception as e:
                    logger.error(f"[Watcher] Error processing file [{file_path}]: {e}")
                    time.sleep(5)
                    continue
                else:
                    logger.debug(f"[Watcher] Processed file [{file_path}]")
            time.sleep(1)
