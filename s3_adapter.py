'''Used to communicate with a S3 compatible server'''

from io import IOBase
import os
import json
from minio import Minio
from minio.helpers import ObjectWriteResult


class S3Adapter:
    '''A representation of a S3 compatible server connection

    endpoint, access_key, secret_key, bucket_name are the required to connect to
    the server, can be passed as arguments or as environment variables. If not
    provided, a ValueError will be raised.

    Args:
        endpoint (str): The server endpoint
        access_key (str): The access key to the server
        secret_key (str): The secret key to the server
        bucket_name (str): The bucket name to be used
    '''

    _endpoint = None
    _access_key = None
    _secret_key = None
    _bucket_name = None
    _client = None

    def __init__(
            self,
            endpoint: str = None,
            access_key: str = None,
            secret_key: str = None,
            bucket_name: str = None
    ):
        self._endpoint = endpoint if endpoint else os.environ.get(
            'S3_ENDPOINT')
        self._access_key = access_key if access_key else os.environ.get(
            'S3_ACCESS_KEY')
        self._secret_key = secret_key if secret_key else os.environ.get(
            'S3_SECRET_KEY')

        if not self._endpoint or not self._access_key or not self._secret_key:
            raise ValueError(
                'Missing S3 endpoint, access key, secret key')

        self._client = Minio(self._endpoint,
                             access_key=self._access_key,
                             secret_key=self._secret_key
                             )
        self.bucket = bucket_name if bucket_name else os.environ.get(
            'S3_BUCKET')

    @property
    def bucket(self) -> str:
        '''The bucket name to be used'''

        return self._bucket_name

    @bucket.setter
    def bucket(self, name: str) -> None:
        if name:
            self._bucket_name = name
        elif os.environ.get('S3_BUCKET'):
            self._bucket_name = os.environ.get('S3_BUCKET')
        elif self._bucket_name:
            pass
        else:
            raise ValueError('Missing S3 bucket name')

        _public_read_policy = {
            "Version": '2012-10-17',
            "Statement": [
                {
                    "Sid": 'AddPublicReadCannedAcl',
                    "Principal": '*',
                    "Effect": 'Allow',
                    "Action": ['s3:GetObject'],
                    "Resource": [f"arn:aws:s3:::{self._bucket_name}/*"]
                }
            ]
        }

        found = self._client.bucket_exists(self._bucket_name)
        if not found:
            self._client.make_bucket(self._bucket_name)
        self._client.set_bucket_policy(
            self._bucket_name, json.dumps(_public_read_policy))

    def have(self, file_path: str) -> bool:
        '''Check if a file exists in the server.

        Args:
            file_path (str): The file path to check

        Returns:
            bool: True if the file exists, False otherwise
        '''

        try:
            result = self._client.stat_object(self._bucket_name, file_path)
            if result.etag:
                return True
            else:
                return False
        except Exception as e:
            return False

    def upload(self, source_file: str | IOBase, dest_file: str) -> ObjectWriteResult:
        '''Upload a file to the server.

        Args:
            source_file (str | IOBase): The source file path or an IOBase object representing the file
            dest_file (str): The destination file path

        Returns:
            ObjectWriteResult: The result of the upload
        '''

        if isinstance(source_file, str):
            return self._client.fput_object(
                self._bucket_name, dest_file, source_file,
            )
        else:
            source_file.seek(0, os.SEEK_END)
            size = source_file.tell()
            source_file.seek(0)
            return self._client.put_object(
                self._bucket_name, dest_file, source_file, length=size
            )

    def remove_object(self, file_path: str) -> None:
        '''Remove a file from the server.

        Args:
            file_path (str): The file path to remove
        '''

        self._client.remove_object(self.bucket, file_path)
