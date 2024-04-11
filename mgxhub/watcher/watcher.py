'''Used to watch the work directory for new files and process them'''

import atexit
import fcntl
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

from mgxhub.config import cfg
from mgxhub.db import db
from mgxhub.logger import logger
from mgxhub.processor import FileProcessor


class RecordWatcher:
    '''Watches the work directory for new files and processes them'''

    def __init__(self, max_workers=4):
        '''Initialize the watcher'''

        self.lock_file = "/tmp/mgxhub_record_watcher.lock"
        self.file = open(self.lock_file, 'w', encoding='ascii')

        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # another instance is running
            print("Another watcher instance is running")
            return

        atexit.register(self._remove_lock_file)

        self.work_dir = cfg.get('system', 'uploaddir')
        os.makedirs(self.work_dir, exist_ok=True)

        if self.work_dir and os.path.isdir(self.work_dir):
            self.file_queue = Queue()
            self.max_workers = max_workers
            self.thread = threading.Thread(target=self._watch, daemon=True)
            self.thread.start()
            logger.info(f"[Watcher] Monitoring directory: {self.work_dir}")

    def _remove_lock_file(self):
        '''Remove the lock file'''

        fcntl.flock(self.file, fcntl.LOCK_UN)
        self.file.close()

    def _watch(self):
        '''Watch the work directory for new files and process them'''
        while True:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                self._scan(self.work_dir)
                while not self.file_queue.empty():
                    file_path = self.file_queue.get()
                    executor.submit(self._process_file, file_path)
            time.sleep(1)

    def _process_file(self, file_path):
        '''Process the file'''

        session = db()
        try:
            file_processor = FileProcessor(session, file_path, syncproc=True, s3replace=False, cleanup=True)
            logger.debug(f"[Watcher] {file_path}: {file_processor.result().get('status', 'unknown')}")
            if os.path.isfile(file_path):
                os.remove(file_path)
            # Try remove parent directory if it is empty
            try:
                os.rmdir(os.path.dirname(file_path))
            except OSError:
                pass
        except Exception as e:
            logger.error(f"[Watcher] Error [{file_path}]: {e}")
            # This exception may due to unfinished file writing, so we wait for a while
            time.sleep(2)
            return
        finally:
            session.close()

    def _scan(self, dirpath: str):
        for root, dirs, files in os.walk(dirpath):
            for filename in files:
                file_path = os.path.join(root, filename)
                self.file_queue.put(file_path)
            for inner_dir in dirs:
                inner_path = os.path.join(root, inner_dir)
                self._scan(inner_path)
