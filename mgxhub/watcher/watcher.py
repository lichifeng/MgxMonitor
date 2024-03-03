'''Used to watch the work directory for new files and process them'''

import os
import threading
import time
from mgxhub.handler import FileHandler, DBHandler

class RecordWatcher:
    '''Watches the work directory for new files and processes them'''

    def __init__(self, s3_creds: list = None, db: DBHandler = None):
        self.work_dir = os.getenv('WORK_DIR')
        self.s3_creds = s3_creds
        self.db = db
        print(f"[Watcher] Work directory: {self.work_dir}")
        if self.work_dir and os.path.isdir(self.work_dir):
            print(f"[Watcher] Watching directory: {self.work_dir}")
            self.thread = threading.Thread(target=self._watch, daemon=True)
            self.thread.start()


    def _watch(self):
        while True:
            for filename in os.listdir(self.work_dir):
                file_path = os.path.join(self.work_dir, filename)
                print(f"[Watcher] Found file: {file_path}")
                file_handler = FileHandler(file_path, self.s3_creds, delete_after=True, db_handler=self.db)
                try:
                    file_handler.process()
                    time.sleep(0.05)
                except Exception as e:
                    print(f"[Watcher] Error processing file [{file_path}]: {e}")
                    time.sleep(5)
                    continue
                else:
                    print(f"[Watcher] Processed file [{file_path}]")
            time.sleep(1)