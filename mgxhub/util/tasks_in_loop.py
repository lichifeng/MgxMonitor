'''Run slow tasks in a new loop'''

import asyncio
from typing import Callable


def run_slow_tasks(tasks: list[Callable]):
    '''Run slow tasks in a new loop.

    **This func is designed to run in a new thread.** Called from current thread
    may confilct with existing event loop.

    Args:
        tasks: List of functions to run.

    Returns:
        list: Results of the tasks.
    '''

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    finally:
        loop.close()
