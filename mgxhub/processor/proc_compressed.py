'''Process a compressed file'''

import os
import tempfile
import threading

import patoolib

from mgxhub import cfg, logger

from .allowed_types import ACCEPTED_COMPRESSED_TYPES
from .move2error import move_to_error


def _decompress(filepath: str, cleanup: bool = True) -> True:
    with tempfile.TemporaryDirectory(prefix='unzip_', dir=cfg.get('system', 'uploaddir'), delete=False) as temp_dir:
        try:
            patoolib.extract_archive(filepath, outdir=temp_dir, interactive=False, verbosity=-1)
            if cleanup and os.path.exists(filepath):
                os.remove(filepath)
            return True
        except Exception as e:
            logger.error(f'patoolib error: {e}')
            move_to_error(filepath, 'archivefile')
            return False


def process_compressed(filepath: str, cleanup: bool = True) -> dict:
    '''Process a compressed file

    Compressed file will be extracted to upload directory and be processed by the watcher.

    Args:
        filepath (str): The path of the compressed file.
        cleanup (bool): Whether to delete the file after processing.
    '''

    # Check the file existence
    if not os.path.isfile(filepath):
        return {'status': 'error', 'message': 'file not found'}

    # Check the file type
    fileext = filepath.split('.')[-1].lower()
    if fileext not in ACCEPTED_COMPRESSED_TYPES:
        return {'status': 'error', 'message': 'unsupported file type'}

    # Check the file size
    filesize = os.path.getsize(filepath)
    if filesize > 2 * 1024 * 1024:
        # decompress in another thread
        threading.Thread(target=_decompress, args=(filepath, True)).start()
        return {'status': 'success', 'message': 'big compressed file was queued for processing'}

    decompressed = _decompress(filepath, cleanup)
    if decompressed:
        return {'status': 'success', 'message': 'small compressed file was queued for processing'}

    return {'status': 'error', 'message': 'failed to extract a compressed file'}
