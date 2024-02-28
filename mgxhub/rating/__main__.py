'''Standalone xecutable of elo rating calculator.'''

import os
import sys
import time
import argparse
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from . import EloCalculator

if __name__ == "__main__":
    # Check if the lock file exists, other processes can read the RATING_CALC_LOCK_FILE environment variable to get the lock file path
    LOCK_FILE = os.getenv('RATING_CALC_LOCK_FILE',
                          "/tmp/mgxhub_elo_calc_process.lock")
    if not os.path.exists(LOCK_FILE):
        os.environ['RATING_CALC_LOCK_FILE'] = LOCK_FILE
    else:
        print("Only one instance of the ELO rating calculator can run at a time. Exiting.")
        sys.exit(1)

    start_time = time.time()

    # Create the lock file
    with open(LOCK_FILE, 'w', encoding="ASCII") as file:
        # TODO other processes can read the lock file to check if the process is still running
        # Write current PID to the first line
        pid = os.getpid()
        file.write(str(pid) + "\n")

        # Write current timestamp to the second line
        timestamp = int(time.time())
        file.write(str(timestamp) + "\n")

    try:
        parser = argparse.ArgumentParser(description='Update ELO ratings.')
        parser.add_argument('--db_path', default=os.getenv('SQLITE_PATH',
                            'test_db.sqlite3'), help='Path to SQLite database')
        parser.add_argument('--duration_threshold', default=os.getenv(
            'RATING_DURATION_THRESHOLD', 15 * 60 * 1000), help='Duration threshold for ELO rating update')
        parser.add_argument('--batch_size', default=os.getenv(
            'RATING_CALC_BATCH_SIZE', 100000), help='Batch size for ELO rating update')
        args = parser.parse_args()

        engine = create_engine(f"sqlite:///{args.db_path}", echo=False)
        session = Session(engine)
        elo = EloCalculator(session)
        elo.update_ratings(
            duration_threshold=int(args.duration_threshold), batch_size=int(args.batch_size))
        session.close()
        engine.dispose()
    finally:
        # Remove the lock file
        os.remove(LOCK_FILE)

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)

    # Get the current time
    current_time = datetime.now()

    # Create the log message
    log_message = f"[{current_time}] Duration(seconds): {elapsed_time}"

    # Append the log message to the ratings_calc_log.txt file
    with open("/tmp/ratings_calc_log.txt", "a", encoding="ASCII") as file:
        file.write(log_message + "\n")
    print(log_message)
