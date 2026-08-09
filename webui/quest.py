"""All Quest (Northwestern SLURM cluster) interaction goes through here, as
plain subprocess calls to your system `ssh`/`scp`/`rsync` binaries -- so it
reuses whatever SSH key/agent/config alias already lets `ssh <alias>` work
without a password prompt. No persistent connections, no background polling:
every function here runs once and returns.
"""
from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass, field

from . import config

SSH_TIMEOUT = 20
SBATCH_TIMEOUT = 30
RSYNC_TIMEOUT = 600  # results dirs can be large; sync is an explicit, waited-on action


@dataclass
class CommandResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    cmd: list[str] = field(default_factory=list)

    @property
    def combined_output(self) -> str:
        parts = [p for p in (self.stdout, self.stderr) if p]
        return "\n".join(parts)


def _run(cmd: list[str], timeout: int) -> CommandResult:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return CommandResult(ok=proc.returncode == 0, returncode=proc.returncode,
                              stdout=proc.stdout, stderr=proc.stderr, cmd=cmd)
    except subprocess.TimeoutExpired as e:
        return CommandResult(ok=False, returncode=-1, stdout=e.stdout or "",
                              stderr=f"Timed out after {timeout}s: {e}", cmd=cmd)
    except FileNotFoundError as e:
        return CommandResult(ok=False, returncode=-1, stdout="", stderr=str(e), cmd=cmd)


def ssh_run(remote_command: str, timeout: int = SSH_TIMEOUT) -> CommandResult:
    """Run a single command on Quest over the configured SSH alias."""
    alias = config.quest_ssh_alias()
    return _run(["ssh", alias, remote_command], timeout=timeout)


def check_connection() -> CommandResult:
    """Smoke test: `ssh <alias> whoami`. Use this before anything else to
    confirm config.yaml's ssh_alias is set up correctly."""
    return ssh_run("whoami")


def upload_file(local_path: str, remote_path: str) -> CommandResult:
    """Copy a single file (the generated .sh) up to Quest, creating the
    remote parent directory first."""
    alias = config.quest_ssh_alias()
    remote_dir = remote_path.rsplit("/", 1)[0]
    mkdir_result = ssh_run(f"mkdir -p {shlex.quote(remote_dir)}")
    if not mkdir_result.ok:
        return mkdir_result
    return _run(["scp", local_path, f"{alias}:{remote_path}"], timeout=SSH_TIMEOUT)


def submit_job(remote_script_path: str) -> tuple[CommandResult, str | None]:
    """Runs `sbatch <remote_script_path>` on Quest. Returns (result, job_id)
    where job_id is parsed from 'Submitted batch job <id>', or None on failure."""
    result = ssh_run(f"sbatch {shlex.quote(remote_script_path)}", timeout=SBATCH_TIMEOUT)
    job_id = None
    if result.ok:
        m = re.search(r"Submitted batch job (\d+)", result.stdout)
        if m:
            job_id = m.group(1)
    return result, job_id


def squeue_status(job_id: str) -> list[dict]:
    """Live queue status for a job (and its array tasks, if any). Empty list
    if the job isn't in the queue anymore (finished, failed, or never
    existed) -- check sacct_status for those."""
    fmt = "%i|%j|%T|%M|%l|%R"
    result = ssh_run(f"squeue -j {shlex.quote(job_id)} --noheader --format='{fmt}'")
    if not result.ok:
        return []
    return _parse_pipe_rows(result.stdout, ["job_id", "name", "state", "elapsed", "time_limit", "reason"])


def sacct_status(job_id: str) -> list[dict]:
    """Historical/accounting status for a job and its array tasks (works for
    running, completed, and failed jobs alike). More reliable than squeue
    once a job has left the live queue."""
    fmt = "JobID,JobName,State,Elapsed,ExitCode"
    result = ssh_run(
        f"sacct -j {shlex.quote(job_id)} --noheader --parsable2 --format={fmt}"
    )
    if not result.ok:
        return []
    return _parse_pipe_rows(result.stdout, ["job_id", "name", "state", "elapsed", "exit_code"], sep="|")


def _parse_pipe_rows(raw: str, columns: list[str], sep: str = "|") -> list[dict]:
    rows = []
    for line in raw.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split(sep)
        if len(parts) < len(columns):
            parts += [""] * (len(columns) - len(parts))
        rows.append(dict(zip(columns, parts)))
    return rows


def peek_log(remote_log_path: str, lines: int = 50) -> CommandResult:
    """One-shot tail of a job's .out file -- not a live stream, just a
    snapshot of the last N lines on demand."""
    return ssh_run(f"tail -n {int(lines)} {shlex.quote(remote_log_path)}")


def rsync_pull(remote_dir: str, local_dir: str) -> CommandResult:
    """Pull remote_dir's contents down into local_dir (creates it if needed).
    Trailing slash on the remote side means 'contents of', matching typical
    rsync results-sync usage."""
    alias = config.quest_ssh_alias()
    import os
    os.makedirs(local_dir, exist_ok=True)
    remote = f"{alias}:{remote_dir.rstrip('/')}/"
    return _run(["rsync", "-avz", remote, local_dir], timeout=RSYNC_TIMEOUT)
