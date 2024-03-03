import unittest
import logging
import os
from mgxhub.logger import logger
from mgxhub.config import cfg

class TestLoggerFactory(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg

    def test_get(self):
        print(id(logger))
        self.assertIsInstance(logger, logging.Logger)

    def test_loglevel(self):
        print(id(logger))
        loglevel_str = self.cfg.get('system', 'loglevel', fallback='INFO')
        loglevel = getattr(logging, loglevel_str.upper(), logging.INFO)
        self.assertEqual(logger.level, loglevel)

    def test_handler(self):
        print(id(logger))
        log_dir = self.cfg.get('system', 'logdir')
        if self.cfg.get('system', 'logdest') == 'console':
            logger.info('log to console')
            self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
        elif os.path.isdir(log_dir):
            logger.info(f'log_dir: {log_dir} exists')
            self.assertIsInstance(logger.handlers[0], logging.handlers.TimedRotatingFileHandler)
        
        logger.info(f'Testing logger with level {logger.level} and handler {logger.handlers[0]}')

if __name__ == '__main__':
    unittest.main()