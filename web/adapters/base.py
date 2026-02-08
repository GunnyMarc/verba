import os
import sys
from contextlib import contextmanager


@contextmanager
def suppress_stdout():
    """Context manager to silence noisy pipeline output."""
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout


def make_progress_callback(job):
    """Factory that returns a callback for updating job progress."""

    def callback(progress, message=""):
        pct = int(progress * 100) if isinstance(progress, float) and progress <= 1.0 else int(progress)
        job.update_progress(pct, message)

    return callback
