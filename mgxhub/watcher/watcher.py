'''Used to watch the queue and process tasks in it.

I tried to monitor a directory for new files and process them. But there's a
problem with the the solution. When a file is being written to the directory,
the watcher will try to process it. This will cause an error because the file is
not yet complete. Adding a delay before processing the file will make the
process slow. Solutions like **pyinotify** or **watchdog** makes the process
complex.

**Watcher** is hence not a good idea I think.

My solution is limiting the file input to an API endpoint, upload files with
SFTP or other methods are not considered. When a file is uploaded, the API will
add a task to a queue. Workers will then process the tasks in the queue.

Under this design, files in upload dir should only from _decompress() of
`proc_compressed.py`.
'''

import atexit
import fcntl
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from mgxhub import cfg, logger, proc_queue
from mgxhub.db import db_raw
from mgxhub.processor import FileProcessor

from .scanner import scan


class RecordWatcher:
    '''Watches the queue and process tasks in it.'''

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

        scan(self.work_dir)

        if self.work_dir and os.path.isdir(self.work_dir):
            self.q = proc_queue
            self.max_workers = max_workers
            self.thread = threading.Thread(target=self._watch, daemon=True)
            self.thread.start()
            logger.info("[Watcher] Monitoring queue...")

    def _remove_lock_file(self):
        '''Remove the lock file'''

        fcntl.flock(self.file, fcntl.LOCK_UN)
        self.file.close()

    def _watch(self):
        '''Watch the work directory for new files and process them'''
        while True:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while not self.q.empty():
                    task_path = self.q.get()
                    executor.submit(self._process_file, task_path)
            time.sleep(1)

    def _process_file(self, file_path):
        '''Process the file'''

        session = db_raw()
        try:
            file_processor = FileProcessor(session, file_path, syncproc=True, s3replace=False, cleanup=True)
            logger.debug(f"[Watcher] {file_path}: {file_processor.result().get('status', 'unknown')}")
            if os.path.isfile(file_path):
                os.remove(file_path)

            # Try remove parent directory if it is empty
            parentdir = os.path.dirname(file_path)
            if os.path.isdir(parentdir) and not os.listdir(parentdir):
                try:
                    os.rmdir(parentdir)
                except OSError:
                    pass
        except Exception as e:
            logger.error(f"[Watcher] Error [{file_path}]: {e}")
        finally:
            self.q.task_done()
            session.close()
