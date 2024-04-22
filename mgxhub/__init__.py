'''mgxhub main source code'''

import queue

from .config import cfg
from .logger import logger

proc_queue = queue.Queue()
