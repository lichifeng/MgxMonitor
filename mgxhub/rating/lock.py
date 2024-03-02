'''Used to operate lock file for rating calculation process'''

import os
import time
import sys
import subprocess
import signal


class RatingLock:
    """Used to operate lock file for rating calculation process."""

    _pid: int | None = None
    _started_time: int | None = None
    _lock_file: str | None = None

    def __init__(self):
        self._lock_file = os.getenv(
            'RATING_CALC_LOCK_FILE', "/tmp/mgxhub_elo_calc_process.lock")
        if os.path.exists(self._lock_file):
            with open(self._lock_file, 'r', encoding="ASCII") as file:
                lines = file.readlines()
                self._pid = int(lines[0].strip())
                self._started_time = int(lines[1].strip())

    @property
    def pid(self):
        """Return the PID in the lock file."""
        return self._pid

    @property
    def started_time(self):
        """Return the timestamp in the lock file."""
        return self._started_time

    def rating_running(self) -> bool:
        """Check if the rating calculation process is running.
        An alias for self.pid_exists().
        """
        return self.pid_exists()

    @property
    def lock_file_path(self) -> str | None:
        """Return the path of the lock file.
        DOESN'T MEAN THE FILE EXISTS!
        """

        return self._lock_file

    def lock_file_exists(self) -> bool:
        """Check if the lock file exists."""
        return os.path.exists(self._lock_file)

    def pid_exists(self) -> bool:
        """Check if the PID exists in the system.
        
        Reference:
            https://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid-in-python
        """

        if self.pid is None:
            return False
        try:
            os.kill(self.pid, 0)
        except OSError:
            return False

        return True

    @property
    def time_elapsed(self) -> float | None:
        """Return the time elapsed since the timestamp in the lock file."""

        if self.started_time is None:
            return None
        return time.time() - self.started_time

    def start_calc(self):
        """Start the rating calculation process."""

        if self.rating_running():
            pass
        else:
            # Get the path of the current Python interpreter
            current_interpreter = sys.executable

            # Start a new thread to run the mgxhub.rating module, it does not
            # wait for the new thread to finish
            subprocess.Popen([current_interpreter, '-m', 'mgxhub.rating'])

    def unlock(self, force=False):
        """Remove the lock file. 
        If force, the process will be terminated before removing the lock file.
        """

        if force:
            self.terminate_process()

        if self.lock_file_exists() and not self.pid_exists():
            try:
                os.remove(self.lock_file_path)
            except FileNotFoundError:
                pass

    def terminate_process(self):
        """Terminate the process with the PID in the lock file.
        
        `os.waitpid` 函数用于等待子进程结束，并返回子进程的退出状态。
        如果不调用 `os.waitpid`，那么即使子进程已经结束，它仍然会在系
        统中以僵尸进程的形式存在，直到父进程调用 `waitpid` 或结束。这
        可能会导致资源泄漏。代码创建了子进程，并且希望在子进程结束时进
        行一些清理工作，就应该调用 `os.waitpid`。如果代码没有创建子进
        程，或者不关心子进程的退出状态，那不需要。
        """

        if self.pid and self.pid_exists():
            os.kill(self.pid, signal.SIGTERM)
            os.waitpid(self._pid, 0)
