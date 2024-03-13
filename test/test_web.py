'''Comprehansive test suite for the web API.'''

import hashlib
import os
import unittest

from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

from main import app
from mgxhub import cfg
from mgxhub.auth import LOGGED_IN_CACHE
from mgxhub.config import Config

# Change this value to specify another test configuration file or modify options
# in this one for testing
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'testconf.ini')


class TestWebAPIs(unittest.TestCase):
    '''Comprehensive test suite for the web API.'''

    def setUp(self):
        # Set the configuration file for testing
        Config().load(CONFIG_FILE)

        self.client = TestClient(app)

    def test_logout_all_users(self):
        '''webapi/routers/auth_logoutall.py'''

        # Add a user to the cache to simulate a logged in
        LOGGED_IN_CACHE['test_user'] = 'test_token'

        response = self.client.get(
            "/auth/logoutall",
            auth=HTTPBasicAuth(
                cfg.get('wordpress', 'username'),
                cfg.get('wordpress', 'password')
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "All users was logged out"})

        # Check that the cache is empty after the logout
        self.assertEqual(len(LOGGED_IN_CACHE), 0)

    def test_list_online_users(self):
        '''webapi/routers/auth_onlineusers.py'''

        # Add a user to the cache to simulate a logged in
        user_hash = hashlib.sha256((cfg.get('wordpress', 'username') +
                                   cfg.get('wordpress', 'password')).encode()).hexdigest()

        response = self.client.get(
            "/auth/onlineusers",
            auth=HTTPBasicAuth(
                cfg.get('wordpress', 'username'),
                cfg.get('wordpress', 'password')
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(user_hash, response.json())

        # Clean up the cache after the test
        del LOGGED_IN_CACHE[user_hash]

    def test_backup_sqlite(self):
        '''webapi/routers/backup_sqlite.py

        NOTIC: Remember clean the backup directory after the test
        '''

        response = self.client.get(
            "/system/backup/sqlite",
            auth=HTTPBasicAuth(
                cfg.get('wordpress', 'username'),
                cfg.get('wordpress', 'password')
            )
        )
        # Check the status code
        self.assertIn(response.status_code, [202, 404])
        # Check the content
        if response.status_code == 202:
            self.assertEqual(response.json(), "Backup command sent")
        else:
            self.assertEqual(response.json(), "No valid SQLite3 database found")


if __name__ == '__main__':
    unittest.main()
