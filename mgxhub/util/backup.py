'''Backup SQLite3 database'''

import os
import shutil
import uuid
from datetime import datetime

import apsw

from mgxhub import cfg, logger


def sqlite3backup(src_path: str = '', dest_path: str = '') -> None:
    '''Backup SQLite3 database'''

    if not src_path:
        src_path = cfg.get('database', 'sqlite')
    if not dest_path:
        # Backup file names like `mgxhub-2021-08-01.sqlite3`
        backup_file = f"mgxhub-{datetime.now().strftime('%Y-%m-%d')}.sqlite3"
        dest_path = os.path.join(cfg.get('system', 'backupdir'), backup_file)
        if os.path.exists(dest_path):
            logger.warning(f"Triggered a duplicated backup command to '{dest_path}'")
            return
        os.makedirs(cfg.get('system', 'backupdir'), exist_ok=True)

    with apsw.Connection(src_path) as src_conn, apsw.Connection(dest_path) as dest_conn:
        with dest_conn.backup("main", src_conn, "main") as backup:
            while not backup.done:
                backup.step(200)  # copy up to 200 pages each time
                # print(f'\r{(backup.pagecount-backup.remaining)/backup.pagecount*100:.2f}%', end='')

    # zip the backup file, then remove the original
    root_dir = os.path.dirname(dest_path)
    base_dir = os.path.basename(dest_path)
    zip_base = dest_path
    if os.path.exists(dest_path + '.zip'):
        zip_base += '_' + uuid.uuid4().hex[:6]
    shutil.make_archive(zip_base, 'zip', root_dir, base_dir)
    logger.info(f"SQLite3 backup to {dest_path}.zip, original size: {os.path.getsize(
        dest_path)} bytes, zipped size: {os.path.getsize(f'{dest_path}.zip')} bytes")
    os.remove(dest_path)
