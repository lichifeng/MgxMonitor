import unittest

from mgxhub.auth import WPRestAPI
from mgxhub.config import Config


class TestWPRestAPI(unittest.TestCase):

    def test_authenticate(self):

        Config().load('testconf.ini')

        wp_api = WPRestAPI('user', 'password')

        # Act
        result = wp_api.authenticate()
        self.assertTrue(result)

        result = wp_api.authenticate(True)
        self.assertTrue(result)

        result = wp_api.need_admin_login()
        self.assertTrue(result)

        result = wp_api.need_user_login()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
