#!/usr/bin/env bash
# One-shot setup for running the tEBC models on Quest.
#
#   1. ssh <netid>@quest.it.northwestern.edu
#   2. git clone https://github.com/Dylan-TerMolen/RatInABox.git ~/ratinabox
#   3. (from your laptop) scp rat0313_pos.mat <netid>@quest.it.northwestern.edu:~/ratinabox/
#   4-5. cd ~/ratinabox && ./hannah_setup.sh
#
# Installs everything inside this folder (Hannahs-CEBRAs, Python venv, results, job logs),
# queues one independent-model test job with the bioreal parameters, then queues one 216-task
# sweep per model that only starts if the test job succeeds. SLURM settings match Dylan's past
# Quest sweeps.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
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
    [ -f "$MATLAB_FILE" ] || die "copy rat0313_pos.mat to $MATLAB_FILE first (step 3)"
}

ask_email() {
    if [ -z "${USER_EMAIL+x}" ]; then
        USER_EMAIL=""
        [ -t 0 ] && read -rp "Your email for job notifications ($DYLAN_EMAIL is always included): " USER_EMAIL
    fi
    MAIL_USERS=$DYLAN_EMAIL${USER_EMAIL:+,$USER_EMAIL}
}

clone_cebras() {
    if [ -d "$CEBRAS/.git" ]; then git -C "$CEBRAS" pull -q --ff-only
    else git clone -q https://github.com/Dylan-TerMolen/Hannahs-CEBRAs.git "$CEBRAS"; fi
}

install_python_env() {
    echo "== Installing Python environment (first run takes a few minutes) =="
    [ -x "$VENV/bin/python" ] || "$(find_python)" -m venv "$VENV"
    "$VENV/bin/pip" install -q --upgrade pip
    "$VENV/bin/pip" install -q -e "$CEBRAS" -e "$ROOT" python-dotenv
}

write_env_file() {
    cat > "$ROOT/ratinabox/hsw/.env" <<EOF
MATLAB_FILE_PATH=$MATLAB_FILE
SAVE_DIRECTORY=$RESULTS
TRAINING_DATA_DIR=$ROOT/training_data
ENVIRONMENT="Slurm"
EOF
}

sweep_axes() {  # $1 = model -> grid axes, fastest-varying first (matches the old slurm/*_sweep.sh)
    case $1 in
        arousal_mediated) echo "PTRC PCS HOLDOVER" ;;  # no percent_task_in_response axis; holdover swept instead
        *) echo "PTIR PTRC PCS" ;;                      # holdover pinned at 1.0
    esac
}

write_job() {  # write_job <model> <experiment> <num_iters> <axes> <fixed params> -> path of the sbatch script
    local model=$1 experiment=$2 num_iters=$3 axes=$4 fixed=$5 job=$JOBS/$2.sh
    {
        echo "#!/bin/bash"
        echo "#SBATCH --account=p32472"
        echo "#SBATCH --partition=gengpu"
        echo "#SBATCH --gres=gpu:a100:1"
        echo "#SBATCH --nodes=1"
        echo "#SBATCH --ntasks=1"
        echo "#SBATCH --mem=8GB"
        echo "#SBATCH --time=2:00:00"
        echo "#SBATCH --job-name=$experiment"
        if [ -n "$axes" ]; then
            echo "#SBATCH --array=0-215%4"
            echo "#SBATCH --output=$LOGS/$experiment.%A_%a.out"
        else
            echo "#SBATCH --output=$LOGS/$experiment.%j.out"
        fi
        echo "#SBATCH --mail-type=ALL"
        echo "#SBATCH --mail-user=$MAIL_USERS"
        echo
        echo "MODEL=$model EXPERIMENT=$experiment NUM_ITERS=$num_iters"
        echo "$fixed"
        echo "AXES=($axes)"
        echo "PYTHON=$VENV/bin/python MAIN=$ROOT/ratinabox/hsw/main.py"
        cat <<'EOF'
GRID=(0.6 0.8 0.2 0.4 1.0 0.0)  # each swept axis takes these 6 values; 6^3 = 216 array tasks

IDX=${SLURM_ARRAY_TASK_ID:-0}
for axis in "${AXES[@]}"; do
    printf -v "$axis" '%s' "${GRID[$((IDX % ${#GRID[@]}))]}"
    IDX=$((IDX / ${#GRID[@]}))
done
echo "model=$MODEL ptir=${PTIR:-n/a} responsive=$PTRC place=$PCS holdover=$HOLDOVER iters=$NUM_ITERS"

ARGS=(--model_type "$MODEL" --experiment "$EXPERIMENT"
      --percent_task_responsive_cells "$PTRC" --percent_is_task_responsive_distribution fixed
      --percent_place_cells "$PCS" --holdovers "$HOLDOVER" --num_iters "$NUM_ITERS")
[ -z "$PTIR" ] || ARGS+=(--percent_task_in_response_values "$PTIR" --percent_task_in_response_dist fixed)

"$PYTHON" "$MAIN" "${ARGS[@]}"
EOF
    } > "$job"
    echo "$job"
}

write_test_job() {  # bioreal params (paper/params/bioreal.yaml); ptir/holdover there are still provisional
    write_job independent "independent_bioreal_test_$TAG" 1 "" "PTIR=0.5 PTRC=0.4 PCS=0.2 HOLDOVER=1.0"
}

write_sweep_job() {  # $1 = model
    write_job "$1" "${1}_sweep_$TAG" 3 "$(sweep_axes "$1")" 'PTIR="" HOLDOVER=1.0'
}

confirm_submit() {
    local answer=${SUBMIT:-}
    [ -n "$answer" ] || { [ -t 0 ] && read -rp "Submit the test job + 3 sweeps (sweeps wait for the test to pass)? [y/N]: " answer; }
    [[ $answer =~ ^[Yy] ]]
}

submit_jobs() {
    mkdir -p "$JOBS" "$LOGS"
    local test_job sweeps=() model job test_id
    test_job=$(write_test_job)
    for model in "${MODELS[@]}"; do sweeps+=("$(write_sweep_job "$model")"); done
    printf '== Generated ==\n'; printf '  %s\n' "$test_job" "${sweeps[@]}"
    confirm_submit || { echo "Not submitted. Submit later with: sbatch <script> for each file above."; return; }
    test_id=$(sbatch --parsable "$test_job")
    echo "  test: job $test_id"
    for job in "${sweeps[@]}"; do
        echo "  $(basename "$job" .sh): job $(sbatch --parsable --dependency=afterok:"$test_id" "$job")"
    done
    squeue -u "$USER"
    echo "If the test job fails, the sweeps stay pending (DependencyNeverSatisfied): scancel them and check $LOGS/."
}

check_prerequisites
ask_email
clone_cebras
install_python_env
write_env_file
submit_jobs
echo "Job logs: $LOGS/   Results: $RESULTS/{model}_results/"
