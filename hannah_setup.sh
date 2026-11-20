#!/usr/bin/env bash
# One-shot setup for running the tEBC model sweeps on Quest. On a Quest login node:
#
#   mkdir -p ~/ratinabox && cp rat0313_pos.mat ~/ratinabox/
#   bash <(curl -fsSL https://raw.githubusercontent.com/Dylan-TerMolen/RatInABox/main/hannah_setup.sh)
#
# Everything lives in ~/ratinabox: both repos, the Python venv, results and job logs. Runs the
# test suite, then submits one 216-task sweep per model (independent, place_dependent,
# arousal_mediated) with the same SLURM settings as Dylan's past Quest sweeps. Safe to re-run.
set -euo pipefail

ROOT=$HOME/ratinabox
REPO=$ROOT/RatInABox
CEBRAS=$ROOT/Hannahs-CEBRAs
VENV=$ROOT/venv
MATLAB_FILE=$ROOT/rat0313_pos.mat
RESULTS=$ROOT/results
JOBS=$ROOT/jobs
LOGS=$ROOT/slurm_out
TAG=$(date +%m%d%y)
MODELS=(independent place_dependent arousal_mediated)
DYLAN_EMAIL=dptermolen@gmail.com  # always notified alongside whoever runs this

die() { echo "ERROR: $*" >&2; exit 1; }

find_python() {  # Quest's system python3 is too old; prefer miniconda's
    local python=python3
    [ -x "$HOME/miniconda3/bin/python3" ] && python=$HOME/miniconda3/bin/python3
    "$python" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null \
        || die "need Python 3.9+ (install miniconda to ~/miniconda3)"
    echo "$python"
}

check_prerequisites() {
    command -v sbatch >/dev/null || die "sbatch not found -- run this on a Quest login node"
    [ -f "$MATLAB_FILE" ] || die "copy rat0313_pos.mat to $MATLAB_FILE first"
}

ask_email() {
    if [ -z "${USER_EMAIL+x}" ]; then
        USER_EMAIL=""
        [ -t 0 ] && read -rp "Your email for job notifications ($DYLAN_EMAIL is always included): " USER_EMAIL
    fi
    MAIL_USERS=$DYLAN_EMAIL${USER_EMAIL:+,$USER_EMAIL}
}

clone_or_pull() {  # $1 = GitHub repo name, $2 = destination
    if [ -d "$2/.git" ]; then git -C "$2" pull -q --ff-only
    else git clone -q "https://github.com/Dylan-TerMolen/$1.git" "$2"; fi
}

install_python_env() {
    [ -x "$VENV/bin/python" ] || "$(find_python)" -m venv "$VENV"
    "$VENV/bin/pip" install -q --upgrade pip
    "$VENV/bin/pip" install -q -e "$CEBRAS" -e "$REPO" python-dotenv pytest
}

write_env_file() {
    cat > "$REPO/ratinabox/hsw/.env" <<EOF
MATLAB_FILE_PATH=$MATLAB_FILE
SAVE_DIRECTORY=$RESULTS
TRAINING_DATA_DIR=$ROOT/training_data
ENVIRONMENT="Slurm"
EOF
}

run_tests() {
    echo "== Running test suite =="
    (cd "$REPO" && "$VENV/bin/python" -m pytest ratinabox/hsw/tests -q -p no:warnings)
}

sweep_axes() {  # $1 = model -> grid axes, fastest-varying first (matches the old slurm/*_sweep.sh)
    case $1 in
        arousal_mediated) echo "PTRC PCS HOLDOVER" ;;  # no percent_task_in_response axis; holdover swept instead
        *) echo "PTIR PTRC PCS" ;;                      # holdover pinned at 1.0
    esac
}

write_sweep_job() {  # $1 = model -> path of the generated sbatch script
    local model=$1 job=$JOBS/${1}_sweep_$TAG.sh
    cat > "$job" <<EOF
#!/bin/bash
#SBATCH --account=p32472
#SBATCH --partition=gengpu
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-215%4
#SBATCH --mem=8GB
#SBATCH --time=2:00:00
#SBATCH --job-name=${model}_sweep
#SBATCH --output=$LOGS/${model}_sweep.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=$MAIL_USERS

MODEL=$model
EXPERIMENT=${model}_sweep_$TAG
AXES=($(sweep_axes "$model"))
PYTHON=$VENV/bin/python
MAIN=$REPO/ratinabox/hsw/main.py
EOF
    cat >> "$job" <<'EOF'
GRID=(0.6 0.8 0.2 0.4 1.0 0.0)  # 6^3 = 216 combinations, one per array task
HOLDOVER=1.0 PTIR=""

IDX=$SLURM_ARRAY_TASK_ID
for axis in "${AXES[@]}"; do
    printf -v "$axis" '%s' "${GRID[$((IDX % ${#GRID[@]}))]}"
    IDX=$((IDX / ${#GRID[@]}))
done
echo "Task $SLURM_ARRAY_TASK_ID: model=$MODEL ptir=${PTIR:-n/a} responsive=$PTRC place=$PCS holdover=$HOLDOVER"

ARGS=(--model_type "$MODEL" --experiment "$EXPERIMENT"
      --percent_task_responsive_cells "$PTRC" --percent_is_task_responsive_distribution fixed
      --percent_place_cells "$PCS" --holdovers "$HOLDOVER" --num_iters 3)
[ -z "$PTIR" ] || ARGS+=(--percent_task_in_response_values "$PTIR" --percent_task_in_response_dist fixed)

"$PYTHON" "$MAIN" "${ARGS[@]}"
EOF
    echo "$job"
}

confirm_submit() {
    local answer=${SUBMIT:-}
    [ -n "$answer" ] || { [ -t 0 ] && read -rp "Submit 3 sweeps x 216 tasks now? [y/N]: " answer; }
    [[ $answer =~ ^[Yy] ]]
}

submit_sweeps() {
    mkdir -p "$JOBS" "$LOGS"
    local jobs=() model job
    for model in "${MODELS[@]}"; do jobs+=("$(write_sweep_job "$model")"); done
    printf '== Generated ==\n'; printf '  %s\n' "${jobs[@]}"
    confirm_submit || { echo "Not submitted. Submit later with: sbatch <script> for each file above."; return; }
    for job in "${jobs[@]}"; do echo "  $(basename "$job"): job $(sbatch --parsable "$job")"; done
    squeue -u "$USER"
}

check_prerequisites
ask_email
mkdir -p "$ROOT"
clone_or_pull RatInABox "$REPO"
clone_or_pull Hannahs-CEBRAs "$CEBRAS"
install_python_env
write_env_file
run_tests
submit_sweeps
echo "Job logs: $LOGS/   Results: $RESULTS/{model}_results/"
