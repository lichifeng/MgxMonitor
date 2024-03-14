'''Used to handle the file uploaded or found in monitored directory.'''
# pylint: disable=R0903

import asyncio
import base64
import os
import random
import shutil
import string
import tempfile
import threading
import zipfile
from datetime import datetime
from io import BytesIO

import patoolib
from PIL import Image

from mgxhub import cfg, logger
from mgxhub.db.operation import add_game
from mgxhub.parser import parse
from mgxhub.rating import RatingLock
from mgxhub.storage import S3Adapter


class FileProcessor:
    '''Used to handle the file uploaded or found in monitored directory.

    The main process() needs to be called manually.

    Args:
        file_path (str): The path of the file to be processed.
        s3_creds (list, optional): The credentials for the S3 bucket. Defaults to None.
        s3_replace (bool, optional): Whether to replace the file if it already exists in the S3 bucket. Defaults to False.
        map_dir (str, optional): The directory to save the map images. Defaults to "".
        delete_after (bool, optional): Whether to delete the file after processing. Defaults to False.
    '''
    ACCEPTED_RECORD_TYPES = ['mgx', 'mgx2', 'mgz', 'mgl', 'msx', 'msx2', 'aoe2record']
    ACCEPTED_COMPRESSED_TYPES = ['zip', 'rar', '7z']
    OSS_RECORD_DIR = cfg.get('s3', 'recorddir')

    _file_path = None
    _file_extension = None
    _current_file = None
    _current_extension = None

    _invalid_count = 0
    _valid_count = 0

    _s3_conn = None
    _s3_replace = False

    _map_dir = None

    _delete_after = False

    def __init__(
            self,
            file_path: str,
            s3_replace: bool = False,
            delete_after: bool = False
    ):
        '''Initialize the FileHandler.'''

        self._file_path = file_path
        self._set_current_file(file_path)
        self._file_extension = self._current_extension
        self._delete_after = delete_after

        self._map_dir = cfg.get('system', 'mapdir')

        try:
            self._s3_conn = S3Adapter(**cfg.s3)
        except Exception as e:
            logger.debug(f's3 error: {e}')
        self._s3_replace = s3_replace

    def _clean_file(self, file_path: str | None = None) -> None:
        '''Delete the file if it exists and delete_after is set to True.'''

        # print("Function _clean_file was called from:")
        # traceback.print_stack(limit=2)  # limit=2 will print the caller and the line that called this function

        if not self._delete_after:
            return

        if file_path:
            self._set_current_file(file_path)

        if not self._current_file:
            return

        if os.path.isfile(self._current_file):
            os.remove(self._current_file)

        if os.path.isdir(self._current_file):
            try:
                os.rmdir(self._current_file)
            except OSError:
                logger.warning(f'Try removing non-empty dir: {self._current_file}')
                return self.process(self._current_file)

        # This part is kind of dirty, referring to a variable possibly defined
        # in some inherited class??
        # See ./file_obj_processor.py
        tmpdir_from_child = getattr(self, '_tmpdir', None)
        if tmpdir_from_child and os.path.isdir(tmpdir_from_child):
            shutil.rmtree(tmpdir_from_child)
            return

    def _set_current_file(self, file_path: str) -> None:
        '''Set the current file and its extension.'''

        self._current_file = file_path
        self._current_extension = file_path.split('.')[-1].lower()

    def process(self, file_path: str | None = None) -> dict:
        '''Start processing the file and return the result.

        Args:
            file_path (str, optional): The path of the file to be processed. Defaults to None.

        Returns:
            dict: The result of the processing.
        '''

        if file_path:
            self._set_current_file(file_path)
        # NOTE Following codes should never use file_path directly, but use self._current_file

        if os.path.isdir(self._current_file):
            self._process_directory(self._current_file)
            self._clean_file(self._current_file)
            return {'status': 'success', 'message': 'directory was processed'}

        if self._current_extension in self.ACCEPTED_RECORD_TYPES:
            async_run = self._current_file == self._file_path
            logger.info(f'Process: {self._current_file}')
            return self._process_record(self._current_file, async_run=async_run, opts='-b')

        if self._current_extension in self.ACCEPTED_COMPRESSED_TYPES:
            logger.info(f'Process(compressed): {self._current_file}')
            return self._process_compressed(self._current_file)

        self._clean_file()
        return {'status': 'invalid', 'message': 'unsupported file type'}

    # NOTICE:
    # THE EXAMPLE BELOW FAILED, WAS LEFT FOR FUTURE REFERENCE
    #
    # def _slow_tasks(self, tasks):
    #     '''Run the slow tasks asynchronously.

    #     _slow_tasks 函数会使用 asyncio 的事件循环来并发地运行多个任务。这些任务
    #     会在同一个线程中并发运行，而不是在新的线程中运行。这是因为 asyncio 是基
    #     于单线程的协程模型，它使用事件循环来调度任务，而不是创建新的线
    #     程。_slow_tasks 函数本身是一个阻塞函数，它会阻塞调用它的线程，直到所有的
    #     任务都完成。这是因为 loop.run_until_complete(asyncio.gather(*tasks)) 会
    #     阻塞当前线程，直到所有的任务都完成。所以，_slow_tasks 函数会在同一个线程
    #     中并发地运行多个任务，并且会阻塞调用它的线程，直到所有的任务都完成。这
    #     样，你可以在 _slow_tasks 函数返回后，确保所有的任务都已经完成。
    #     '''

    #     loop_found = False
    #     try:
    #         loop = asyncio.get_running_loop()
    #         loop_found = True
    #     except RuntimeError:
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)

    #     try:
    #         loop.run_until_complete(asyncio.gather(*tasks))
    #     except Exception as e:
    #         print(f'Error in slow tasks: {e}')
    #     finally:
    #         if not loop_found:
    #             loop.close()

    def _slow_tasks(self, tasks):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*tasks))
        finally:
            loop.close()

    def _process_record(self, record_path: str, async_run: bool = False, opts: str = '') -> dict:
        '''Process the record file and return the result.

        Input file should be a record file, not a compressed package or other types.

        Args:
            reccord_path (str): The path of the record file to be processed.

        Returns:
            dict: The result of the processing.
        '''

        parsed_result = parse(record_path, opts=opts)

        if parsed_result['status'] in ['error', 'invalid']:
            logger.warning(f'Invalid record: {record_path}')
            self._invalid_count += 1
            self._clean_file(record_path)
            return parsed_result

        ############################################################
        ############# Asyncable Procedures Start ###################

        tasks = []

        if 'map' in parsed_result and 'base64' in parsed_result['map'] and self._map_dir:
            tasks.append(self._save_map(parsed_result['guid'], parsed_result['map']['base64']))

        tasks.append(self._save_to_db(parsed_result))

        if self._s3_conn:
            try:
                # raise Exception('Test error')
                tasks.append(self._save_to_s3(record_path, parsed_result))
                if 'map' in parsed_result and 'base64' in parsed_result['map']:
                    tasks.append(self._save_map_s3(parsed_result['guid'], parsed_result['map']['base64']))
            except Exception as e:
                logger.error(f'_save_to_s3 error: {e}')
                self._move_to_error(record_path)
        else:
            self._move_to_error(record_path)
            # self._clean_file(record_path)

        # Me:
        # 为什么我在对这个类单独测试时没有找到消息循环，但是通过fastapi调用的时候能找到？

        # Copilot:
        # 这是因为FastAPI在内部使用了Starlette，Starlette在启动时会创建一个事件循
        # 环，并在整个应用的生命周期中运行这个事件循环。当你通过FastAPI调用你的代
        # 码时，你的代码就在这个事件循环中运行，所以`asyncio.get_running_loop()`能
        # 够找到一个正在运行的事件循环。然而，当你单独测试你的类时，如果你没有手动
        # 创建一个事件循环，那么`asyncio.get_running_loop()`就无法找到一个正在运行
        # 的事件循环，因为默认情况下，Python的主线程不会创建事件循环。
        # try:
        #     loop = asyncio.get_running_loop()
        #     print('Running loop found')
        # except RuntimeError:
        #     print('No running loop')

        # NOTICE:
        # THE EXAMPLE BELOW FAILED, WAS LEFT FOR FUTURE REFERENCE
        #
        # if async_run:
        #     threading.Thread(target=self._slow_tasks, args=(tasks,)).start()
        # else:
        #     self._slow_tasks(tasks)

        slow_tasks_thd = threading.Thread(target=self._slow_tasks, args=(tasks,))
        slow_tasks_thd.start()
        if not async_run:
            slow_tasks_thd.join(100)

        ############### Asyncable Procedures End ###################
        ############################################################

        self._valid_count += 1
        return parsed_result

    def _process_directory(self, dir_path: str) -> None:
        '''Process the directory and its files recursively.

        Args:
            dir_path (str): The path of the directory to be processed.
        '''

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                self.process(file_path)
            for inner_dir in dirs:
                inner_path = os.path.join(root, inner_dir)
                self._process_directory(inner_path)
                self._clean_file(inner_path)

    def _process_compressed(self, zip_path: str) -> dict:
        '''Extract the compressed file and process the files inside.

        Args:
            zip_path (str): The path of the compressed file to be processed.

        Returns:
            dict: The result of the processing.
        '''

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # raise Exception('Test error')
                patoolib.extract_archive(zip_path, outdir=temp_dir, interactive=False, verbosity=-1)
            except Exception as e:
                logger.error(f'patoolib error: {e}')
                self._move_to_error(zip_path)
                return {'status': 'invalid', 'message': 'failed to extract a compressed file'}

            self._process_directory(temp_dir)
            self._clean_file(zip_path)

        return {'status': 'success', 'message': 'compressed file was scaduled for processing'}

    async def _save_to_db(self, data: dict) -> tuple[str, str]:
        '''Save the parsed data to the database.

        Args:
            data (dict): The parsed data of the record file.

        Returns:
            str: The result of the saving.
        '''

        try:
            result = add_game(data)
            logger.info(f'[DB] Add: {result}')
            if result[0] in ['success', 'updated']:
                RatingLock().start_calc(schedule=True)
        except Exception as e:
            logger.error(f'_save_to_db error: {e}')
            result = 'error', str(e)

        return result

    async def _save_to_s3(
        self,
        record_path: str,
        data: object
    ) -> str:
        '''Save the record file to the S3 bucket.

        Args:
            record_path (str): The path of the record file to be saved.
            data (object): The parsed data of the record file.

        Returns:
            str: The result of the saving.
        '''

        required_keys = ['md5', 'fileext', 'guid']
        if not all(key in data for key in required_keys):
            logger.warning(f'Bad game meta: {record_path}')
            self._move_to_error(record_path)
            return 'OSS_BAD_META'

        if self._s3_conn.have(self.OSS_RECORD_DIR + data['md5'] + '.zip') and not self._s3_replace:
            self._clean_file(record_path)
            return 'OSS_FILE_EXISTS'

        with tempfile.TemporaryFile(suffix='.zip') as temp_file:
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as z:
                if 'version' in data and 'code' in data['version']:
                    version_code = data['version']['code']
                else:
                    version_code = 'UNKNOWN'
                if 'matchup' in data:
                    matchup = data['matchup']
                else:
                    matchup = 'UNKNOWN'
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if 'gameTime' in data and isinstance(data['gameTime'], int):
                    played_at = datetime.fromtimestamp(
                        data['gameTime']).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    played_at = current_time
                packed_name = f"{version_code}_{matchup}_{data['md5'][:5]}{data['fileext']}"
                comment_template = f'''
Age of Empires II record

Version: {version_code}
Matchup: {matchup}

GUID: {data['guid']}
MD5 : {data['md5']}
(Maybe) Played at: {played_at}

Collected by aocrec.com
Parsed by {data['parser']}
Packed at {current_time}
'''
                z.write(record_path, packed_name)
                z.comment = comment_template.encode('ASCII')

            try:
                result = self._s3_conn.upload(
                    temp_file,
                    self.OSS_RECORD_DIR + data['md5'] + '.zip',
                    metadata={
                        'guid': data['guid'],
                        'md5': data['md5'],
                        'parser': data['parser'],
                        'played_at': played_at,
                        'version': version_code,
                        'matchup': matchup
                    }
                )
                logger.info(f'Uploaded: {result.object_name}')
                self._clean_file(record_path)
                return 'OSS_UPLOAD_SUCCESS'
            except Exception as e:
                logger.error(f'_save_to_s3 error: {e}')
                self._move_to_error(record_path)
                return 'OSS_UPLOAD_ERROR'

    async def _save_map(self, basename: str, base64_str: str) -> str:
        '''Save the map image to the directory.

        Args:
            basename (str): The basename of the record file.
            base64_str (str): The base64 string of the map image.

        Returns:
            str: The result of the saving.
        '''

        if not self._map_dir:
            return 'MAP_DIR_NOT_SET'

        try:
            os.makedirs(self._map_dir, exist_ok=True)
            img = Image.open(BytesIO(base64.b64decode(base64_str)))
            img.save(os.path.join(self._map_dir, basename + '.png'))
            return 'MAP_SAVE_SUCCESS'
        except Exception as e:
            logger.error(f'_save_map error: {e}, basename(guid): {basename}, current file: {self._current_file}')
            return 'MAP_SAVE_ERROR'

    async def _save_map_s3(self, basename: str, base64_str: str) -> str:
        '''Save the map image to the S3 bucket.

        Args:
            basename (str): The basename of the record file.
            base64_str (str): The base64 string of the map image.

        Returns:
            str: The result of the saving.
        '''

        if not self._s3_conn:
            return 'OSS_CONN_NOT_SET'

        try:
            img = Image.open(BytesIO(base64.b64decode(base64_str)))
            buf = BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            result = self._s3_conn.upload(
                buf, cfg.get('system', 'mapdirS3') + basename + '.png',
                content_type='image/png'
            )
            logger.debug(f'Map uploaded: {result.object_name}')
            return 'OSS_MAP_UPLOAD_SUCCESS'
        except Exception as e:
            logger.error(f'_save_map_s3 error: {e}')
            return 'OSS_MAP_UPLOAD_ERROR'

    def _move_to_error(self, file_path: str, copy: bool = False) -> str:
        '''Move the file to the error directory.

        Args:
            file_path (str): The path of the file to be moved.
        '''

        error_dir = cfg.get('system', 'errordir')
        os.makedirs(error_dir, exist_ok=True)

        file_name = os.path.basename(file_path)
        new_file_name = file_name
        file_exists = os.path.isfile(os.path.join(error_dir, new_file_name))
        while file_exists:
            prefix = ''.join(random.choices(string.ascii_lowercase, k=3))
            new_file_name = f"{prefix}_{file_name}"
            file_exists = os.path.isfile(os.path.join(error_dir, new_file_name))

        new_file_path = os.path.join(error_dir, new_file_name)
        if copy:
            shutil.copy2(file_path, new_file_path)
        else:
            shutil.move(file_path, new_file_path)

        return new_file_path
