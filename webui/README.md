# Quest Job Runner (local web UI)

A local web app for building, submitting, and tracking SLURM jobs on Quest
(Northwestern's HPC cluster) across this repo (`ratinabox/hsw`) and
[hannahs-cebras](https://github.com/dylan-termolen/hannahs-cebras), without
hand-editing `.sh` files or babysitting `squeue` over SSH.

## What it does

- **Script picker** — auto-detects a script's CLI params (real `argparse`
  introspection for `ratinabox/hsw/main.py`, static source scanning for
  hannahs-cebras' one-off scripts) and renders a form instead of you typing a
  command from memory.
- **SLURM generator** — turns the filled-in form into a `.sh` script matching
  the account/partition/GPU conventions already used by hand in `SLURM/*.sh`
  and `hsw/*/SLURM_*.sh`. Any param can be marked "grid" (comma-separated
  values) to sweep it as a `--array` job, same row-major mapping pattern as
  `SLURM_place_dependent.sh`.
- **Upload existing `.sh`** — for scripts not covered by the generator, upload
  one you already wrote; it's submitted as-is.
- **Upload + queue** — pipes the generated/uploaded script to Quest over ssh
  and runs `sbatch`, tracked in a local SQLite job registry.
- **Status** — job progress (squeue/sacct, array-task breakdown) is **only**
  ever checked when you click "Refresh status". Nothing polls in the
  background. A "Peek log" button takes a one-off `tail -n 50` snapshot of a
  job's output file, also on demand -- not a live stream.
- **Sync** — pulls a repo's results dir down from Quest via `rsync`, only when
  you click "Sync now".
- **Results** — browse synced CSVs, pick X/Y columns, plot (a small
  dependency-free canvas plotter, no charting library, no CDN).

## Setup

1. **Edit `webui/config.yaml`** — every `CHANGE_ME` needs a real value:
   - `quest.host` / `quest.username` / `quest.identity_file` — the same
     three pieces your `slurm` alias and `slurmresults` function already use
     (`ssh -i <identity_file> <username>@<host>`). No `~/.ssh/config` alias
     needed; the app builds the full ssh/rsync command itself. The app
     never prompts for a password -- it relies on that key working
     passwordlessly, same as your alias does today.
   - `repos.*.local_path` / `repos.*.remote_path` — where each repo lives on
     this machine vs. on Quest.
   - `slurm_defaults` — pre-filled into every generated script; override
     per-job in the UI.

2. **Install dependencies** into the same conda env you run the analysis
   scripts from (script introspection imports the repos' own modules):

   ```bash
   conda activate ratinabox
   pip install -r webui/requirements.txt
   ```

3. **Run it**:

   ```bash
   uvicorn webui.app:app --reload --port 8420
   ```

   Open http://127.0.0.1:8420

4. **Sanity-check Quest access** before trying to submit anything: `ssh -i
   ~/.ssh/slurm_pk tfl2886@quest.it.northwestern.edu whoami` should return
   your NetID with no prompt. If it doesn't, upload/queue/sync will fail
   (gracefully -- you'll see the error in the UI, not a crash) until that's
   sorted.

## Quest touch points

Every place this app talks to Quest, all in `webui/quest.py`, all via `ssh
-i <identity_file> <user>@<host> '<command>'` or `rsync -avz -e "ssh -i
<identity_file>" ...` (no `scp`, no other tool, no persistent connection):

| Action (UI button)          | Router                    | Remote command(s) |
|---|---|---|
| Upload to Quest              | `POST /jobs/{id}/upload`  | one ssh call: `cat > <path>` (script piped over stdin). Falls back to a one-time `mkdir -p <dir>` + retry only if the write fails (e.g. the very first upload to a repo) |
| sbatch (queue)                | `POST /jobs/{id}/queue`   | one ssh call: `sbatch <path>` |
| Refresh status                | `POST /jobs/{id}/refresh` | one ssh call running both `squeue -j <id> ...` and `sacct -j <id> ...` |
| Peek log (last 50 lines)      | `GET /jobs/{id}/peek-log` | one ssh call: `tail -n 50 <path>` |
| Sync now                      | `POST /sync`              | one rsync call: `rsync -avz -e "ssh -i <identity_file>" <host>:<remote_results_dir>/ <local_results_dir>` |

That's the complete list -- five buttons, one round trip each in steady
state (upload takes a second one-off round trip only the first time a
repo's `webui_slurm/` directory doesn't exist yet), nothing else in the app
shells out anywhere. `quest.check_connection()` (a plain `ssh ...
whoami`) exists as a smoke test but isn't wired to a button yet.

## Design notes / current limits

- Single-user, local-only tool. No auth, no multi-tenancy -- don't expose
  this port beyond localhost.
- `webui/data/jobs.db` (SQLite) is the only persistence; delete it to reset.
- hannahs-cebras script introspection is static (`ast`-based source scanning
  of `add_argument(...)` calls) since those scripts run analysis code at
  import time and can't be safely imported. A script whose args aren't
  literal strings (built dynamically) won't be picked up -- use "Upload
  existing .sh" for those.
- No live log streaming or auto-refreshing status by design -- every
  Quest-touching action (refresh status, peek log, sync) is a single
  explicit, on-demand round trip.
