'''Logger'''

import json
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from mgxhub.config import Config


class JsonFormatter(logging.Formatter):
    '''Dump log message to JSON format.'''

    def format(self, record):
        log_message = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'message': record.getMessage(),
            'source': record.pathname,
            'line': record.lineno
        }
        return json.dumps(log_message)


class Logger():
    '''Logger.

    1. system.logdest = console: log to console, otherwise log to file
    2. log file dirs will be created if not exists

    Example:
    ```python
    from mgxhub.logger import LoggerFactory

    logger = LoggerFactory().get()
    logger.info('Hello, world!')
    ```
    '''

    def __init__(self):
        cfg = Config().config
        self._logger = logging.getLogger('mgxhub')

        loglevel_str = cfg.get('system', 'loglevel', fallback='INFO')
        loglevel = getattr(logging, loglevel_str.upper(), logging.INFO)
        self._logger.setLevel(loglevel)

        if cfg.get('system', 'logdest', fallback='console').lower() == 'console':
            handler = logging.StreamHandler()
        else:
            log_dir = cfg.get('system', 'logdir')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'mgxhub.log')
            handler = TimedRotatingFileHandler(log_file, when='W0', interval=1)

        handler.setLevel(loglevel)
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.debug(f'Logger initialized with level: {loglevel}, handler: {handler.__class__.__name__}')

    def get(self) -> logging.Logger:
        '''Get logger instance.

        Only one instance of logger is created across the application.
        '''

        return self._logger
