'''Used to watch the work directory for new files and process them'''

import atexit
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

    def __init__(self, max_workers=2):
        '''Initialize the watcher'''

        self.lock_file = "/tmp/mgxhub_record_watcher.lock"
        if os.path.exists(self.lock_file):
            with open(self.lock_file, "r", encoding="ascii") as file:
                pid = int(file.read())
                try:
                    os.kill(pid, 0)
                except OSError:  # No such process
                    os.remove(self.lock_file)
                else:  # Process exists
                    return

        with open(self.lock_file, "w", encoding="ascii") as file:
            file.write(str(os.getpid()))

        atexit.register(self._remove_lock_file)

        self.work_dir = cfg.get('system', 'uploaddir')
        os.makedirs(self.work_dir, exist_ok=True)

        if self.work_dir and os.path.isdir(self.work_dir):
            self.file_queue = Queue()
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            self.thread = threading.Thread(target=self._watch, daemon=True)
            self.thread.start()
            logger.info(f"[Watcher] Monitoring directory: {self.work_dir}")

    def _remove_lock_file(self):
        '''Remove the lock file'''
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)

    def _watch(self):
        '''Watch the work directory for new files and process them'''

        while True:
            self._scan(self.work_dir)
            while not self.file_queue.empty():
                file_path = self.file_queue.get()
                self.executor.submit(self._process_file, file_path)
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
