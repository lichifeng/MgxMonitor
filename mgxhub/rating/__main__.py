'''Standalone xecutable of elo rating calculator.'''

import os
import sys
import time
import argparse
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from mgxhub.config import cfg
from mgxhub.logger import logger
from . import EloCalculator

if __name__ == "__main__":
    # Check if the lock file exists, other processes can read the RATING_CALC_LOCK_FILE environment variable to get the lock file path
    LOCK_FILE = cfg.get('rating', 'lockfile')

    if os.path.exists(LOCK_FILE):
        logger.debug("Only one instance of the ELO rating calculator can run at a time. Exiting.")
        sys.exit(1)

    start_time = time.time()

    # Create the lock file
    with open(LOCK_FILE, 'w', encoding="ASCII") as file:
        # Other processes can read the lock file to check if the process is still running
        # Write current PID to the first line
        pid = os.getpid()
        file.write(str(pid) + "\n")

        # Write current timestamp to the second line
        timestamp = int(time.time())
        file.write(str(timestamp) + "\n")

    try:
        parser = argparse.ArgumentParser(description='Update ELO ratings.')
        parser.add_argument('--db_path', default=cfg.get('database', 'sqlite'), help='Path to SQLite database')
        parser.add_argument('--duration_threshold', default=cfg.get('rating', 'durationthreshold'), help='Duration threshold for ELO rating update')
        parser.add_argument('--batch_size', default=cfg.get('rating', 'batchsize'), help='Batch size for ELO rating update')
        args = parser.parse_args()

        engine = create_engine(f"sqlite:///{args.db_path}", echo=False)
        session = Session(engine)
        elo = EloCalculator(session)
        elo.update_ratings(
            duration_threshold=int(args.duration_threshold),
            batch_size=int(args.batch_size)
            )
        session.close()
        engine.dispose()
    finally:
        os.remove(LOCK_FILE)

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)

    # Get the current time
    current_time = datetime.now()

    # Create the log message
    log_message = f"Rating calculated, duration: {elapsed_time}"

    logger.info(log_message)
