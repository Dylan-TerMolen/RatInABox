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

-- One row per SLURM array task (one per grid-parameter combination) within
-- a job -- see grid_parser.py. A non-swept job still gets exactly one row
-- (array_task_index=0, params_json='{}'). log_file_path is filled in by the
-- sync-triggered matching pass (routers/sync.py), not at creation time.
CREATE TABLE IF NOT EXISTS job_iterations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    array_task_index INTEGER NOT NULL,
    params_json TEXT NOT NULL,
    log_file_path TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(job_id, array_task_index)
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


def set_array_count(job_id: int, array_count: int) -> None:
    with _cursor() as (conn, cur):
        cur.execute("UPDATE jobs SET array_count=? WHERE id=?", (array_count, job_id))


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


# ---- job iterations ---------------------------------------------------------

def replace_job_iterations(job_id: int, combos: list[dict]) -> None:
    """Delete this job's existing iteration rows (if any -- e.g. a
    'Recompute iterations' re-run) and insert one fresh row per combo, in
    order. combos: list of {flag_name: value} dicts, index = array task id."""
    with _cursor() as (conn, cur):
        cur.execute("DELETE FROM job_iterations WHERE job_id=?", (job_id,))
        now = _now()
        cur.executemany(
            """INSERT INTO job_iterations (job_id, array_task_index, params_json, created_at)
               VALUES (?, ?, ?, ?)""",
            [(job_id, i, json.dumps(combo), now) for i, combo in enumerate(combos)],
        )


def list_job_iterations(job_id: int) -> list[sqlite3.Row]:
    with _cursor() as (conn, cur):
        cur.execute("SELECT * FROM job_iterations WHERE job_id=? ORDER BY array_task_index", (job_id,))
        return cur.fetchall()


def list_unmatched_iterations(job_id: int | None = None) -> list[sqlite3.Row]:
    """Iterations with no log_file_path yet, optionally scoped to one job.
    Used by the post-sync matching pass so it doesn't re-check ones already
    matched."""
    with _cursor() as (conn, cur):
        if job_id is not None:
            cur.execute("SELECT * FROM job_iterations WHERE job_id=? AND log_file_path IS NULL", (job_id,))
        else:
            cur.execute("SELECT * FROM job_iterations WHERE log_file_path IS NULL")
        return cur.fetchall()


def set_iteration_log_path(iteration_id: int, log_path: str) -> None:
    with _cursor() as (conn, cur):
        cur.execute("UPDATE job_iterations SET log_file_path=? WHERE id=?", (log_path, iteration_id))


def iteration_match_counts() -> dict[int, tuple[int, int]]:
    """{job_id: (matched, total)} across all jobs, for the jobs list page."""
    with _cursor() as (conn, cur):
        cur.execute(
            """SELECT job_id, COUNT(*) AS total, SUM(CASE WHEN log_file_path IS NOT NULL THEN 1 ELSE 0 END) AS matched
               FROM job_iterations GROUP BY job_id"""
        )
        return {row["job_id"]: (row["matched"] or 0, row["total"]) for row in cur.fetchall()}


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
