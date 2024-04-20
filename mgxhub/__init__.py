'''mgxhub main source code'''

import queue

from .config import cfg
from .db import db
from .logger import logger

proc_queue = queue.Queue()
