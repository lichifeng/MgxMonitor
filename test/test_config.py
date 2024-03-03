import unittest
import os
import configparser
from mgxhub.config.default import DefaultConfig

class TestDefaultConfig(unittest.TestCase):
    def setUp(self):
        self.default_config = DefaultConfig()

    def test_init(self):
        self.assertIsInstance(self.default_config.config, configparser.ConfigParser)
        self.assertIn('system', self.default_config.config)
        self.assertIn('database', self.default_config.config)
        self.assertIn('s3', self.default_config.config)
        self.assertIn('rating', self.default_config.config)

    def test_project_root(self):
        print(f'project_root: {self.default_config.project_root()}')
        self.assertTrue(os.path.exists(self.default_config.project_root()))

    def test_write(self):
        test_file = os.path.join(self.default_config.project_root(), 'test.ini')
        self.default_config.write('test.ini')
        self.assertTrue(os.path.exists(test_file))
        os.remove(test_file)

if __name__ == '__main__':
    unittest.main()