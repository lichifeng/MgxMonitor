'''Used to communicate with a S3 compatible server'''

from io import IOBase
import os
import json
from minio import Minio
from minio.helpers import ObjectWriteResult
from mgxhub.logger import logger


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
    _accesskey = None
    _secretkey = None
    _region = None
    _bucket = None
    _virtual_host_style = False
    _client = None


    def __init__(
            self,
            endpoint: str = None,
            accesskey: str = None,
            secretkey: str = None,
            region: str | None = None,
            bucket: str | None = None
    ):
        self._endpoint = endpoint
        self._accesskey = accesskey
        self._secretkey = secretkey
        self._region = region
        self._bucket = bucket

        if not self._endpoint or not self._accesskey or not self._secretkey:
            raise ValueError('Missing S3 endpoint || access key || secret key')

        self._client = Minio(self._endpoint,
                             access_key=self._accesskey,
                             secret_key=self._secretkey,
                             region=self._region
                             )
        self.set_bucket()


    @property
    def bucket(self) -> str:
        '''The bucket name to be used'''

        return self._bucket
    

    def set_bucket(self) -> None:
        '''Set the bucket policy to public read'''

        # if self.bucket is blank string, use part before the first dot of endpoint as bucket name
        if not self._bucket:
            self._bucket = self._endpoint.split('.')[0]
            self._virtual_host_style = True

        _public_read_policy = {
            "Version": '2012-10-17',
            "Statement": [
                {
                    "Sid": 'AddPublicReadCannedAcl',
                    "Principal": '*',
                    "Effect": 'Allow',
                    "Action": ['s3:GetObject'],
                    "Resource": [f"arn:aws:s3:::{self._bucket}/*"]
                }
            ]
        }

        found = self._client.bucket_exists(self._bucket)
        if not found:
            self._client.make_bucket(self._bucket)
        self._client.set_bucket_policy(
            self._bucket, json.dumps(_public_read_policy))


    def have(self, file_path: str) -> bool:
        '''Check if a file exists in the server.

        Args:
            file_path (str): The file path to check

        Returns:
            bool: True if the file exists, False otherwise
        '''

        try:
            result = self._client.stat_object(self._bucket, file_path)
            return bool(result.etag)
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
                self._bucket, dest_file, source_file,
            )
        else:
            source_file.seek(0, os.SEEK_END)
            size = source_file.tell()
            source_file.seek(0)
            return self._client.put_object(
                self._bucket, dest_file, source_file, length=size
            )


    def remove_object(self, file_path: str) -> None:
        '''Remove a file from the server.

        Args:
            file_path (str): The file path to remove
        '''

        self._client.remove_object(self.bucket, file_path)
        logger.warning(f'[S3] Removed {file_path} from {self.bucket}')
