"""Every touch point this app has with Quest lives in this one file, and all
of it goes through exactly two external tools -- the same two you already
use by hand (your `slurm` alias and `slurmresults` function):

  - `ssh -i <identity_file> <username>@<host> '<command>'` for anything that
    runs a command on Quest (upload, sbatch, squeue/sacct, tail -n).
  - `rsync -avz -e "ssh -i <identity_file>" ...` for pulling results down.

No `scp`, no `~/.ssh/config` alias, no persistent/background connection --
every function here is one subprocess call that runs once and returns. The
complete list of functions below IS the complete list of ways this app talks
to Quest; nothing else in webui/ shells out anywhere.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

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


def _run(cmd: list[str], timeout: int, input_bytes: bytes | None = None) -> CommandResult:
    try:
        if input_bytes is not None:
            proc = subprocess.run(cmd, input=input_bytes, capture_output=True, timeout=timeout)
            stdout, stderr = proc.stdout.decode(errors="replace"), proc.stderr.decode(errors="replace")
        else:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            stdout, stderr = proc.stdout, proc.stderr
        return CommandResult(ok=proc.returncode == 0, returncode=proc.returncode,
                              stdout=stdout, stderr=stderr, cmd=cmd)
    except subprocess.TimeoutExpired as e:
        raw = e.stdout or b""
        stdout = raw.decode(errors="replace") if isinstance(raw, bytes) else raw
        return CommandResult(ok=False, returncode=-1, stdout=stdout,
                              stderr=f"Timed out after {timeout}s: {e}", cmd=cmd)
    except FileNotFoundError as e:
        return CommandResult(ok=False, returncode=-1, stdout="", stderr=str(e), cmd=cmd)


def _ssh_base_args() -> list[str]:
    return ["ssh", "-i", config.quest_identity_file(), config.quest_target()]


def ssh_run(remote_command: str, timeout: int = SSH_TIMEOUT) -> CommandResult:
    """Run one command on Quest. Every other ssh-based function below is
    just this, with a specific remote_command."""
    return _run(_ssh_base_args() + [remote_command], timeout=timeout)


def check_connection() -> CommandResult:
    """Smoke test: `ssh -i <identity_file> <username>@<host> whoami`. Run
    this before anything else to confirm config.yaml's quest: block matches
    your real SSH setup."""
    return ssh_run("whoami")


def upload_file(local_path: str, remote_path: str) -> CommandResult:
    """Copy a single file (the generated .sh) up to Quest. Uses ssh + `cat`
    (piping the file over stdin) rather than a separate scp process, so
    upload is still just the one ssh mechanism -- mkdir and write happen in
    the same remote command / same round trip."""
    remote_dir = remote_path.rsplit("/", 1)[0]
    content = Path(local_path).read_bytes()
    remote_command = f"mkdir -p {shlex.quote(remote_dir)} && cat > {shlex.quote(remote_path)}"
    return _run(_ssh_base_args() + [remote_command], timeout=SSH_TIMEOUT, input_bytes=content)


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


_SACCT_MARKER = "---SACCT---"


def job_status(job_id: str) -> dict:
    """Progress for a job and its array tasks. One ssh round trip runs both
    squeue (live queue state) and sacct (accounting state, still populated
    after a task leaves the live queue) and returns both -- squeue's rows
    win where a task appears in both, since it's the fresher of the two."""
    squeue_fmt = "%i|%j|%T|%M|%l|%R"
    sacct_fmt = "JobID,JobName,State,Elapsed,ExitCode"
    remote_command = (
        f"squeue -j {shlex.quote(job_id)} --noheader --format='{squeue_fmt}'; "
        f"echo '{_SACCT_MARKER}'; "
        f"sacct -j {shlex.quote(job_id)} --noheader --parsable2 --format={sacct_fmt}"
    )
    result = ssh_run(remote_command)
    if not result.ok:
        return {"ok": False, "tasks": []}

    live_raw, _, hist_raw = result.stdout.partition(_SACCT_MARKER)
    live = _parse_pipe_rows(live_raw, ["job_id", "name", "state", "elapsed", "time_limit", "reason"])
    hist = _parse_pipe_rows(hist_raw, ["job_id", "name", "state", "elapsed", "exit_code"], sep="|")

    by_task = {r["job_id"]: r for r in hist}
    by_task.update({r["job_id"]: r for r in live})  # squeue is fresher where both have a row
    tasks = sorted(by_task.values(), key=lambda r: r["job_id"])
    return {"ok": True, "tasks": tasks}


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
    """Pull remote_dir's contents down into local_dir (creates it if
    needed) -- the same shape as your `slurmresults` function. Trailing
    slash on the remote side means 'contents of'."""
    os.makedirs(local_dir, exist_ok=True)
    remote = f"{config.quest_target()}:{remote_dir.rstrip('/')}/"
    ssh_cmd = f"ssh -i {shlex.quote(config.quest_identity_file())}"
    return _run(["rsync", "-avz", "-e", ssh_cmd, remote, local_dir], timeout=RSYNC_TIMEOUT)
