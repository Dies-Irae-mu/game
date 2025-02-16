"""
Custom logger configuration for Evennia.
"""
from twisted.logger import FileLogObserver, formatEvent
import os
import time

class ResilientLogFile:
    """
    A simple log file handler that's resilient to shutdown scenarios.
    """
    def __init__(self, filename, directory):
        self.filename = filename
        self.directory = directory
        self.filepath = os.path.join(directory, filename)
        self._file = None
        self._open()

    def _open(self):
        """Open or reopen the file if needed."""
        try:
            if not self._file or self._file.closed:
                os.makedirs(self.directory, exist_ok=True)
                self._file = open(self.filepath, 'a', encoding='utf-8', buffering=1)
        except Exception:
            self._file = None

    def write(self, data):
        """Write data to the file."""
        try:
            self._open()
            if self._file and not self._file.closed:
                self._file.write(data)
                self._file.flush()
        except Exception:
            pass

    def flush(self):
        """Flush the file buffer."""
        try:
            if self._file and not self._file.closed:
                self._file.flush()
        except Exception:
            pass

    def close(self):
        """Close the file."""
        try:
            if self._file and not self._file.closed:
                self._file.close()
        except Exception:
            pass

class ResilientLogObserver(FileLogObserver):
    """
    A log observer that uses our resilient log file.
    """
    def __init__(self, logfile):
        self._outFile = logfile
        self._format = formatEvent

    def __call__(self, event):
        """Format and write an event to the log file."""
        try:
            text = self._format(event)
            if text:
                self._outFile.write(f"{text}\n")
        except Exception:
            pass

def get_robust_file_observer(filename, directory):
    """
    Create and return a robust file observer.
    """
    try:
        log_file = ResilientLogFile(filename, directory)
        return ResilientLogObserver(log_file)
    except Exception as e:
        print(f"Error setting up log observer: {str(e)}")
        return lambda event: None 