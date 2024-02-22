'''Used to handle the file uploaded or found in monitored directory.'''

import os
import asyncio
import base64
import tempfile
import zipfile
import threading
from datetime import datetime
from io import BytesIO
import patoolib
from PIL import Image
from record_parser import parse
from s3_adapter import S3Adapter


class FileHandler:
    '''Used to handle the file uploaded or found in monitored directory.

    The main process() needs to be called manually.

    Args:
        file_path (str): The path of the file to be processed.
        s3_creds (list, optional): The credentials for the S3 bucket. Defaults to None.
        s3_replace (bool, optional): Whether to replace the file if it already exists in the S3 bucket. Defaults to False.
        map_dir (str, optional): The directory to save the map images. Defaults to "".
        delete_after (bool, optional): Whether to delete the file after processing. Defaults to False.
    '''
    ACCEPTED_RECORD_TYPES = ['mgx', 'mgx2',
                             'mgz', 'mgl', 'msx', 'msx2', 'aoe2record']
    ACCEPTED_COMPRESSED_TYPES = ['zip', 'rar', '7z']
    OSS_RECORD_DIR = '/records/'

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
            s3_creds: list = None,
            s3_replace: bool = False,
            map_dir: str = "",
            delete_after: bool = False
    ):
        '''Initialize the FileHandler.'''

        self._file_path = file_path
        self._set_current_file(file_path)
        self._file_extension = self._current_extension
        self._delete_after = delete_after

        if not os.path.isdir(map_dir):
            self._map_dir = os.environ.get('MAP_DIR')
        else:
            self._map_dir = map_dir

        if s3_creds:
            try:
                self._s3_conn = S3Adapter(*s3_creds)
            except Exception as e:
                pass
        self._s3_replace = s3_replace

    def _clean_file(self, file_path: str | None = None) -> None:
        '''Delete the file if it exists and delete_after is set to True.'''

        if not self._delete_after:
            return
        
        if file_path:
            self._set_current_file(file_path)

        if not self._current_file or not os.path.isfile(self._current_file):
            return

        os.remove(self._current_file)

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

        if self._current_extension in self.ACCEPTED_RECORD_TYPES:
            if self._current_file == self._file_path:
                async_run = True
            else:
                async_run = False
            return self._process_record(self._current_file, async_run=async_run, opts='-b')

        if self._current_extension in self.ACCEPTED_COMPRESSED_TYPES:
            return self._process_compressed(self._current_file)

        self._clean_file()
        return {'status': 'invalid', 'message': 'unsupported file type'}

    def _slow_tasks(self, tasks):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*tasks))
        finally:
            loop.close()

    def _process_record(self, reccord_path: str, async_run: bool = False, opts: str = '') -> dict:
        '''Process the record file and return the result.

        Input file should be a record file, not a compressed package or other types.

        Args:
            reccord_path (str): The path of the record file to be processed.

        Returns:
            dict: The result of the processing.
        '''

        parsed_result = parse(reccord_path, opts=opts)

        if parsed_result['status'] in ['error', 'invalid']:
            self._invalid_count += 1
            self._clean_file(reccord_path)
            return parsed_result

        ############################################################
        ############# Asyncable Procedures Start ###################

        tasks = []

        if 'map' in parsed_result and 'base64' in parsed_result['map'] and self._map_dir:
            tasks.append(self._save_map(parsed_result['guid'], parsed_result['map']['base64']))

        tasks.append(self._save_to_db(parsed_result))

        if self._s3_conn:
            try:
                tasks.append(self._save_to_s3(reccord_path, parsed_result))
            except Exception as e:
                # TODO log the error and move the file to error directory
                pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if async_run:
            threading.Thread(target=self._slow_tasks, args=(tasks,)).start()
        else:
            self._slow_tasks(tasks)
            
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

    def _process_compressed(self, zip_path: str) -> dict:
        '''Extract the compressed file and process the files inside.

        Args:
            zip_path (str): The path of the compressed file to be processed.

        Returns:
            dict: The result of the processing.
        '''

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                patoolib.extract_archive(
                    zip_path, outdir=temp_dir, interactive=False, verbosity=-1)
            except Exception as e:
                # TODO log the error and move the file to error directory
                return {'status': 'invalid', 'message': 'failed to extract a compressed file'}

            self._process_directory(temp_dir)
            self._clean_file(zip_path)

        return {'status': 'success', 'message': 'compressed file was scaduled for processing'}

    async def _save_to_db(self, data: dict) -> str:
        '''Save the parsed data to the database.

        Args:
            data (dict): The parsed data of the record file.

        Returns:
            str: The result of the saving.
        '''

        pass

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
                    played_at = datetime.fromtimestamp(data['gameTime']).strftime('%Y-%m-%d %H:%M:%S')
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
                    temp_file, self.OSS_RECORD_DIR + data['md5'] + '.zip')
                # print('uploaded: ' + result.object_name)
                self._clean_file(record_path)
                return 'OSS_UPLOAD_SUCCESS'
            except Exception as e:
                # TODO log the error and move the file to error directory
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
            img = Image.open(BytesIO(base64.b64decode(base64_str)))
            img.save(os.path.join(self._map_dir, basename + '.png'))
            return 'MAP_SAVE_SUCCESS'
        except Exception as e:
            return 'MAP_SAVE_ERROR'
