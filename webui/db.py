"""SQLite persistence for jobs, and sync history.

Single-user, single-machine local tool -- no migrations framework, just
CREATE TABLE IF NOT EXISTS. Delete webui/data/jobs.db to reset.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    repo TEXT NOT NULL,
    script_id TEXT NOT NULL,
    script_display_name TEXT NOT NULL,
    command TEXT NOT NULL,
    params_json TEXT NOT NULL,
    grid_json TEXT,
    array_count INTEGER NOT NULL DEFAULT 1,
    job_name TEXT NOT NULL,
    experiment_tag TEXT,
    slurm_script_local_path TEXT,
    slurm_script_remote_path TEXT,
    sbatch_job_id TEXT,
    uploaded_at TEXT,
    submitted_at TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    last_status_json TEXT,
    last_status_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    repo TEXT NOT NULL,
    remote_path TEXT NOT NULL,
    local_path TEXT NOT NULL,
    success INTEGER NOT NULL,
    output TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    path = config.db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """No migration framework (see module docstring) -- just add any columns
    a pre-existing local jobs.db predates. Each ALTER is wrapped since SQLite
    has no 'ADD COLUMN IF NOT EXISTS'; a 'duplicate column' error just means
    this one's already there."""
    for statement in ["ALTER TABLE jobs ADD COLUMN experiment_tag TEXT"]:
        try:
            conn.execute(statement)
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
    conn.commit()


@contextmanager
def _cursor():
    conn = get_conn()
    try:
        yield conn, conn.cursor()
        conn.commit()
    finally:
        conn.close()


# ---- jobs ----------------------------------------------------------------

def insert_job(*, repo, script_id, script_display_name, command, params: dict,
               grid: dict | None, array_count: int, job_name: str,
               slurm_script_local_path: str, experiment_tag: str | None = None) -> int:
    with _cursor() as (conn, cur):
        cur.execute(
            """INSERT INTO jobs
               (created_at, repo, script_id, script_display_name, command,
                params_json, grid_json, array_count, job_name, experiment_tag,
                slurm_script_local_path, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')""",
            (_now(), repo, script_id, script_display_name, command,
             json.dumps(params), json.dumps(grid) if grid else None,
             array_count, job_name, experiment_tag, slurm_script_local_path),
        )
        return cur.lastrowid


def mark_uploaded(job_id: int, remote_path: str) -> None:
    with _cursor() as (conn, cur):
        cur.execute(
            "UPDATE jobs SET status='uploaded', slurm_script_remote_path=?, uploaded_at=? WHERE id=?",
            (remote_path, _now(), job_id),
        )


def mark_queued(job_id: int, sbatch_job_id: str) -> None:
    with _cursor() as (conn, cur):
        cur.execute(
            "UPDATE jobs SET status='queued', sbatch_job_id=?, submitted_at=? WHERE id=?",
            (sbatch_job_id, _now(), job_id),
        )


def update_status_cache(job_id: int, status_summary: dict) -> None:
    with _cursor() as (conn, cur):
        cur.execute(
            "UPDATE jobs SET last_status_json=?, last_status_at=? WHERE id=?",
            (json.dumps(status_summary), _now(), job_id),
        )


def get_job(job_id: int) -> sqlite3.Row | None:
    with _cursor() as (conn, cur):
        cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        return cur.fetchone()


def list_jobs(repo: str | None = None) -> list[sqlite3.Row]:
    with _cursor() as (conn, cur):
        if repo:
            cur.execute("SELECT * FROM jobs WHERE repo=? ORDER BY id DESC", (repo,))
        else:
            cur.execute("SELECT * FROM jobs ORDER BY id DESC")
        return cur.fetchall()


# ---- sync history ----------------------------------------------------------

def insert_sync_run(*, repo: str, remote_path: str, local_path: str,
                     success: bool, output: str) -> int:
    with _cursor() as (conn, cur):
        cur.execute(
            """INSERT INTO sync_runs (created_at, repo, remote_path, local_path, success, output)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (_now(), repo, remote_path, local_path, int(success), output),
        )
        return cur.lastrowid


def list_sync_runs(repo: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
    with _cursor() as (conn, cur):
        if repo:
            cur.execute("SELECT * FROM sync_runs WHERE repo=? ORDER BY id DESC LIMIT ?", (repo, limit))
        else:
            cur.execute("SELECT * FROM sync_runs ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()
