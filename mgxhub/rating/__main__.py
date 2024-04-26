'''Standalone xecutable of elo rating calculator.'''

import argparse
import asyncio
import fcntl
import os
import sys
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mgxhub.cacher import Cacher
from mgxhub.config import cfg
from mgxhub.logger import logger
from webapi.routers.shortcut_homepage import gen_homepage_data

from . import EloCalculator


async def main(db_path: str, duration_threshold: str, batch_size: str):
    '''Main function for the standalone executable of elo rating calculator.'''

    # Check if the lock file exists, other processes can read the RATING_CALC_LOCK_FILE environment variable to get the lock file path
    LOCK_FILE = cfg.get('rating', 'lockfile')

    if os.path.exists(LOCK_FILE):
        logger.debug("Only one instance of the ELO rating calculator can run at a time. Exiting.")
        sys.exit(1)

    # Create the lock file
    try:
        with open(LOCK_FILE, 'x', encoding="ASCII") as file:
            # Try to lock the file in non-blocking mode
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Other processes can read the lock file to check if the process is still running
            # Write current PID to the first line
            pid = os.getpid()
            file.write(str(pid) + "\n")

            # Write current timestamp to the second line
            timestamp = int(time.time())
            file.write(str(timestamp) + "\n")
    except (BlockingIOError, FileExistsError):
        logger.debug("Race condition: Another instance of the ELO rating calculator is running. Exiting.")
        sys.exit(1)

    if os.path.exists(LOCK_FILE + ".scheduled"):
        logger.debug("The ELO rating will be processed, remove the scheduled signal.")
        try:
            os.remove(LOCK_FILE + ".scheduled")
        except FileNotFoundError:
            pass  # Under multi-threading, the scheduled signal may be removed by another thread

    start_time = time.time()
    logger.debug("Start calculating ELO ratings...")
    try:
        engine = create_engine(f"sqlite:///{db_path}", echo=False, connect_args={'timeout': 60})
        db = Session(engine)
        elo = EloCalculator(db)
        duration_threshold = int(duration_threshold)
        batch_size = int(batch_size)
        try:
            if duration_threshold > 0 and batch_size > 50000:
                elo.update_ratings(duration_threshold, batch_size)
            else:
                elo.update_ratings(15 * 60 * 1000, 150000)

            # TODO Update cache.
            homepage_data_cache_key = "homepage_data_5_30_30"
            cacher = Cacher(db)
            result = await gen_homepage_data(db, 5, 30, 30)
            cacher.purge()
            cacher.set(homepage_data_cache_key, result)

        except Exception as e:
            logger.error(f"Rating Error: {e}")
            db.rollback()
        finally:
            db.close()
            engine.dispose()
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)

    # Create the log message
    log_message = f"Rating calculated, duration: {elapsed_time}"

    logger.debug(log_message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update ELO ratings.')
    parser.add_argument('--db_path', default=cfg.get('database', 'sqlite'), help='Path to SQLite database')
    parser.add_argument('--duration_threshold', default=cfg.get('rating', 'durationthreshold'),
                        help='Duration threshold for ELO rating update')
    parser.add_argument('--batch_size', default=cfg.get('rating', 'batchsize'),
                        help='Batch size for ELO rating update')
    args = parser.parse_args()

    asyncio.run(main(args.db_path, args.duration_threshold, args.batch_size))

    # If another rating calculation is triggered during calculation, it will be
    # scheduled using a scheduled lock file. When the current calculation is
    # finished,  the scheduled calculation will be triggered and the scheduled
    # lock file will be removed in main().
    LOCK_FILE_SCHEDULED = cfg.get('rating', 'lockfile') + ".scheduled"
    if os.path.exists(LOCK_FILE_SCHEDULED):
        asyncio.run(main(args.db_path, args.duration_threshold, args.batch_size))
