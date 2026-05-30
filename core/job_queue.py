"""
AsyncJobQueue — non-blocking background job runner.

The problem with the current design:
  - Email scanning blocks the UI for 10-30 seconds
  - If Gmail is slow, the whole dashboard freezes
  - You can't run multiple scans simultaneously

The solution — a job queue:
  1. User clicks "Scan Gmail" → job is added to queue instantly
  2. Dashboard returns immediately (non-blocking)
  3. Background worker thread processes the job
  4. Results are written to SQLite as they arrive
  5. Dashboard polls for completed results

This is the same pattern used in production systems:
  Celery + Redis, AWS SQS + Lambda, Google Cloud Tasks, etc.
  Here we use Python's built-in threading + queue for simplicity.

Architecture:
  JobQueue (singleton)
    ├── queue.Queue()          — thread-safe FIFO queue
    ├── WorkerThread           — daemon thread consuming jobs
    └── ResultStore (SQLite)   — completed job results

Job states: pending → running → done | failed
"""

import threading
import queue
import uuid
import json
import sqlite3
import traceback
from datetime import datetime
from typing import Callable, Any, Optional
from dataclasses import dataclass, field

from config import DB_PATH


# ── Job dataclass ──────────────────────────────────────────────────────────────

@dataclass
class Job:
    job_type:   str                          # "email_scan", "sms_scan", "learn"
    payload:    dict = field(default_factory=dict)
    job_id:     str  = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status:     str  = "pending"             # pending|running|done|failed
    result:     Any  = None
    error:      str  = ""
    created_at: str  = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


# ── Result store (SQLite) ──────────────────────────────────────────────────────

class JobStore:
    """Persists job status/results to SQLite so the dashboard can poll."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init()

    def _init(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id      TEXT PRIMARY KEY,
                    job_type    TEXT,
                    status      TEXT,
                    payload     TEXT,
                    result      TEXT,
                    error       TEXT,
                    created_at  TEXT,
                    started_at  TEXT,
                    finished_at TEXT
                )
            """)

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def save(self, job: Job):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                job.job_id, job.job_type, job.status,
                json.dumps(job.payload),
                json.dumps(job.result) if job.result else None,
                job.error,
                job.created_at, job.started_at, job.finished_at,
            ))

    def get(self, job_id: str) -> Optional[dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id=?", (job_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_recent(self, limit: int = 10) -> list:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_pending_count(self) -> int:
        with self._conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status='pending'"
            ).fetchone()[0]


# ── Worker thread ──────────────────────────────────────────────────────────────

class WorkerThread(threading.Thread):
    """
    Single daemon thread that pulls jobs from the queue and executes them.
    Daemon=True means it shuts down automatically when the main process exits.
    """

    def __init__(self, job_queue: queue.Queue, job_store: JobStore,
                 handlers: dict):
        super().__init__(daemon=True, name="FinanceAgentWorker")
        self._queue    = job_queue
        self._store    = job_store
        self._handlers = handlers   # job_type → callable
        self._stop     = threading.Event()

    def run(self):
        print("  [Worker] Background job worker started.")
        while not self._stop.is_set():
            try:
                job: Job = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            print(f"  [Worker] Running job {job.job_id} ({job.job_type})")
            job.status     = "running"
            job.started_at = datetime.now().isoformat()
            self._store.save(job)

            try:
                handler = self._handlers.get(job.job_type)
                if handler is None:
                    raise ValueError(f"No handler for job type: {job.job_type}")

                result         = handler(job.payload)
                job.status     = "done"
                job.result     = result
                print(f"  [Worker] Job {job.job_id} done.")

            except Exception as e:
                job.status = "failed"
                job.error  = traceback.format_exc()
                print(f"  [Worker] Job {job.job_id} FAILED: {e}")

            finally:
                job.finished_at = datetime.now().isoformat()
                self._store.save(job)
                self._queue.task_done()

    def stop(self):
        self._stop.set()


# ── Job Queue (main interface) ─────────────────────────────────────────────────

class AsyncJobQueue:
    """
    Public interface for submitting and monitoring background jobs.

    Usage:
        jq = AsyncJobQueue()
        jq.register("email_scan", my_email_handler)
        job_id = jq.submit("email_scan", {"max_emails": 25})
        ...
        status = jq.status(job_id)
    """

    _instance = None   # singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._queue    = queue.Queue()
        self._store    = JobStore()
        self._handlers: dict[str, Callable] = {}
        self._worker   = WorkerThread(self._queue, self._store, self._handlers)
        self._worker.start()
        self._initialized = True

    def register(self, job_type: str, handler: Callable):
        """Register a handler function for a job type."""
        self._handlers[job_type] = handler
        print(f"  [JobQueue] Registered handler for '{job_type}'")

    def submit(self, job_type: str, payload: dict = None) -> str:
        """Submit a job. Returns job_id immediately (non-blocking)."""
        job = Job(job_type=job_type, payload=payload or {})
        self._store.save(job)
        self._queue.put(job)
        print(f"  [JobQueue] Submitted job {job.job_id} ({job_type})")
        return job.job_id

    def status(self, job_id: str) -> Optional[dict]:
        """Poll job status. Returns dict with status, result, error."""
        return self._store.get(job_id)

    def recent_jobs(self, limit: int = 10) -> list:
        """Get recent jobs for the dashboard job monitor."""
        return self._store.get_recent(limit)

    def queue_size(self) -> int:
        return self._queue.qsize()

    def pending_count(self) -> int:
        return self._store.get_pending_count()


# ── Pre-built job handlers ─────────────────────────────────────────────────────

def make_email_scan_handler(storage_tool):
    """Returns a handler that scans Gmail and saves transactions."""
    def handler(payload: dict) -> dict:
        from tools.gmail_tool import GmailTool
        from agents.email_agent import EmailAgent

        max_emails = payload.get("max_emails", 25)
        gmail      = GmailTool()
        agent      = EmailAgent(gmail)
        txns       = agent.scan_and_extract(max_emails=max_emails)

        saved = 0
        for txn in txns:
            storage_tool.save_transaction(txn)
            saved += 1

        return {
            "scanned":     max_emails,
            "found":       len(txns),
            "saved":       saved,
            "timestamp":   datetime.now().isoformat(),
        }
    return handler


def make_learn_handler(storage_tool):
    """Returns a handler that runs the memory learning pass."""
    def handler(payload: dict) -> dict:
        from agents.memory_agent import MemoryAgent
        agent  = MemoryAgent(storage_tool)
        memory = agent.load()
        result = agent.learn_from_history(memory)
        return {"result": result, "timestamp": datetime.now().isoformat()}
    return handler


def make_classifier_retrain_handler(storage_tool):
    """Returns a handler that retrains the ML classifier."""
    def handler(payload: dict) -> dict:
        from ml.classifier import TransactionClassifier
        clf = TransactionClassifier()
        clf.retrain_with_db(storage_tool)
        metrics = clf.evaluate()
        return {"metrics": metrics, "timestamp": datetime.now().isoformat()}
    return handler
