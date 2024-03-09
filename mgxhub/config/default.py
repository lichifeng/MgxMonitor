'''Generate default configuration'''

import configparser
import os


class DefaultConfig:
    '''Default configuration factory.

    1. Provides default configuration values.
    2. Generates a default configuration file.
    '''

    def __init__(self):
        self.config = configparser.ConfigParser(default_section='system')

        # System configuration
        # - Directories need to be created when used
        parser_default = os.path.join(self.project_root(), 'mgxhub', 'parser', 'MgxParser_D_EXE')
        self.config['system'] = {
            'parser': parser_default,
            'workdir': os.path.join(self.project_root(), '__workdir'),  # suppose read-only
            'projectroot': self.project_root()  # suppose read-only
        }
        self.config['system']['mapdir'] = os.path.join(self.config['system']['workdir'], 'map')
        self.config['system']['logdir'] = os.path.join(self.config['system']['workdir'], 'log')
        self.config['system']['uploaddir'] = os.path.join(self.config['system']['workdir'], 'upload')
        self.config['system']['tmpdir'] = os.path.join(self.config['system']['workdir'], 'tmp')
        self.config['system']['tmpprefix'] = 'tmp_'
        self.config['system']['errordir'] = os.path.join(self.config['system']['workdir'], 'error')
        self.config['system']['langdir'] = os.path.join(self.project_root(), 'translations/en/LC_MESSAGES')
        self.config['system']['loglevel'] = 'DEBUG'
        self.config['system']['logdest'] = 'console'  # if not 'console', will try to use log file

        # Database configuration
        self.config['database'] = {}
        self.config['database']['sqlite'] = os.path.join(self.config['system']['workdir'], 'db.sqlite3')

        # S3 configuration
        # - Default values are Minio playground credentials
        self.config['s3'] = {
            'endpoint': 'play.min.io',
            'accesskey': 'Q3AM3UQ867SPQQA43P2F',
            'secretkey': 'zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG',
            'region': 'us-east-1',
            'bucket': 'mgxhub-test-bucket',
            'recorddir': '/records/'
        }

        # Rating configuration
        self.config['rating'] = {
            'durationthreshold': 15 * 60 * 1000,  # 15 minutes
            'batchsize': 150000,
            'lockfile': os.path.join(self.config['system']['workdir'], 'elo_calc_process.lock')
        }

        # WordPress configuration
        self.config['wordpress'] = {
            'url': '',
            'username': '',
            'password': '',
            'login_expire': '15'  # minutes
        }

    def project_root(self) -> str:
        '''Get the project root directory.'''

        if not hasattr(self, '_project_root'):
            script_dir = os.path.dirname(__file__)
            self._project_root = os.path.dirname(os.path.dirname(script_dir))
        return self._project_root

    def write(self, filename: str):
        '''Write the configuration to a file.

        Will **OVERRIDE** the existing one.

        Args:
            filename (str): The path of the file to write to. An absolute path
            or a path relative to the project root.
        '''

        filename = os.path.join(self.project_root(), filename)
        with open(filename, 'x', encoding='utf-8') as file:
            self.config.write(file)
