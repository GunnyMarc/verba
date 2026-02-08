import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Represents a single processing job with thread-safe progress tracking."""

    def __init__(self, job_id: str, job_type: str, input_filename: str, settings: dict):
        self.id = job_id
        self.job_type = job_type
        self.status = JobStatus.PENDING
        self.progress: int = 0
        self.progress_message: str = ""
        self.input_filename = input_filename
        self.settings = settings
        self.result: Optional[dict] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self._lock = threading.Lock()
        self._event = threading.Event()

    def update_progress(self, progress: int, message: str = ""):
        with self._lock:
            self.progress = max(0, min(100, progress))
            if message:
                self.progress_message = message
            self._event.set()

    def start(self):
        with self._lock:
            self.status = JobStatus.RUNNING
            self.started_at = datetime.now(timezone.utc)
            self._event.set()

    def complete(self, result: dict):
        with self._lock:
            self.status = JobStatus.COMPLETED
            self.progress = 100
            self.result = result
            self.completed_at = datetime.now(timezone.utc)
            self._event.set()

    def fail(self, error: str):
        with self._lock:
            self.status = JobStatus.FAILED
            self.error = error
            self.completed_at = datetime.now(timezone.utc)
            self._event.set()

    def wait_for_update(self, timeout: float = 0.5) -> bool:
        result = self._event.wait(timeout=timeout)
        self._event.clear()
        return result

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "job_type": self.job_type,
                "status": self.status.value,
                "progress": self.progress,
                "progress_message": self.progress_message,
                "input_filename": self.input_filename,
                "settings": self.settings,
                "result": self.result,
                "error": self.error,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            }


class JobManager:
    """Thread-safe in-memory job store."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, job_type: str, input_filename: str, settings: dict) -> Job:
        job_id = uuid.uuid4().hex[:8]
        job = Job(job_id, job_type, input_filename, settings)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list[Job]:
        with self._lock:
            return sorted(
                self._jobs.values(),
                key=lambda j: j.created_at,
                reverse=True,
            )

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None
