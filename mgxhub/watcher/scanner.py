'''Scan a directory in upload dir and put file to process queue'''

import os

from mgxhub import proc_queue


def scan(dirpath: str):
    '''Scan a directory in upload dir and put file to process queue

    Args:
        dirpath (str): The directory path to scan.
    '''

    for root, dirs, files in os.walk(dirpath, topdown=False):
        for filename in files:
            file_path = os.path.join(root, filename)
            proc_queue.put(file_path)  # Processor will tried to remove empty parent directory.
        for dir in dirs:
            # Try remove the directory if it is empty, this works because topdown=False
            current_dir_path = os.path.join(root, dir)
            if os.path.isdir(current_dir_path) and not os.listdir(current_dir_path):
                try:
                    os.rmdir(current_dir_path)
                except OSError:
                    pass
