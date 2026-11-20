#!/usr/bin/env bash
# One-shot setup for running the tEBC model sweeps on a SLURM cluster.
#
#   git clone https://github.com/Dylan-TerMolen/RatInABox.git
#   cd RatInABox
#   ./hannah_setup.sh
#
# Asks for your cluster settings, installs everything into a Python venv, clones
# Hannahs-CEBRAs next to this repo, runs the test suite, then submits one 216-task sweep
# per model (independent, place_dependent, arousal_mediated).
#
# Any prompt can be pre-answered by exporting its variable (e.g. SLURM_ACCOUNT=p32472);
# without a terminal, unanswered prompts take their default.
set -euo pipefail

MODELS=(independent place_dependent arousal_mediated)
DYLAN_EMAIL=dptermolen@gmail.com  # always notified alongside whoever runs this

die() { echo "ERROR: $*" >&2; exit 1; }

ask() {  # ask VAR "question" default -- keeps VAR if already exported
    local var=$1 question=$2 default=${3-}
    if [ -z "${!var+x}" ]; then
        local answer=""
        [ -t 0 ] && read -rp "$question [${default:-none}]: " answer
        printf -v "$var" '%s' "${answer:-$default}"
    fi
    echo "  $var=${!var}"
}

find_repo() {
    local repo
    repo=$(git rev-parse --show-toplevel 2>/dev/null) || die "run this from inside your RatInABox clone"
    [ -f "$repo/ratinabox/hsw/main.py" ] || die "$repo is not a RatInABox checkout (no ratinabox/hsw/main.py)"
    echo "$repo"
}

collect_settings() {
    echo "== Settings (press Enter for the default) =="
    # Defaults match Dylan's Quest setup (slurm/*_sweep.sh); Quest's system python3 is too old.
    local default_python=python3
    [ -x "$HOME/miniconda3/bin/python3" ] && default_python=$HOME/miniconda3/bin/python3
    ask PYTHON_BIN "Python 3.9+ to build the venv from" "$default_python"
    ask VENV "Where to create the Python venv" "$REPO/.venv"
    ask MATLAB_FILE_PATH "Path to the position .mat file (e.g. rat0313_pos.mat)" "$REPO/fixtures/rat0313_pos.mat"
    ask SAVE_DIRECTORY "Where decoding results (.log files) go" "$REPO/saved/results"
    ask SLURM_ACCOUNT "SLURM account (--account), blank for none" "p32472"
    ask SLURM_PARTITION "SLURM partition (--partition), blank for none" "gengpu"
    ask SLURM_GRES "GPU request (--gres), blank for CPU-only" "gpu:a100:1"
    ask SLURM_MEM "Memory per task (--mem)" "8G"
    ask SLURM_TIME "Time limit per task (--time)" "2:00:00"
    ask USER_EMAIL "Your email for job notifications ($DYLAN_EMAIL is always included)" ""
    SLURM_MAIL=$DYLAN_EMAIL${USER_EMAIL:+,$USER_EMAIL}
    ask SWEEP_TAG "Suffix for experiment tags" "$(date +%m%d%y)"
    ask CEBRAS_URL "Hannahs-CEBRAs git URL" "https://github.com/Dylan-TerMolen/Hannahs-CEBRAs.git"

    [ -f "$MATLAB_FILE_PATH" ] || die "MATLAB file not found: $MATLAB_FILE_PATH"
    "$PYTHON_BIN" -c 'import sys; sys.exit(sys.version_info < (3, 9))' || die "$PYTHON_BIN is older than 3.9"
    command -v sbatch >/dev/null || die "sbatch not found -- run this on a SLURM login node"
}

clone_cebras() {
    local dir=$1
    if [ -d "$dir/.git" ]; then git -C "$dir" pull --ff-only
    else git clone "$CEBRAS_URL" "$dir"; fi
}

install_python_env() {
    [ -x "$VENV/bin/python" ] || "$PYTHON_BIN" -m venv "$VENV"
    "$VENV/bin/pip" install -q --upgrade pip
    # CPU-only jobs don't need the ~3GB of CUDA libraries the default Linux torch wheel ships.
    [ -n "$SLURM_GRES" ] || "$VENV/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cpu
    "$VENV/bin/pip" install -q -e "$CEBRAS_DIR" -e "$REPO" python-dotenv pytest
}

write_env_file() {
    cat > "$REPO/ratinabox/hsw/.env" <<EOF
MATLAB_FILE_PATH=$MATLAB_FILE_PATH
SAVE_DIRECTORY=$SAVE_DIRECTORY
TRAINING_DATA_DIR=$REPO/saved/training_data
ENVIRONMENT="Slurm"
EOF
}

run_tests() {
    echo "== Running test suite =="
    (cd "$REPO" && "$VENV/bin/python" -m pytest ratinabox/hsw/tests -q)
}

sbatch_header() {  # $1 = model
    echo "#!/bin/bash"
    echo "#SBATCH --job-name=${1}_sweep"
    echo "#SBATCH --array=0-215%4"
    echo "#SBATCH --nodes=1"
    echo "#SBATCH --ntasks=1"
    echo "#SBATCH --mem=$SLURM_MEM"
    echo "#SBATCH --time=$SLURM_TIME"
    echo "#SBATCH --output=$REPO/slurm_out/${1}_sweep.%A_%a.out"
    [ -z "$SLURM_ACCOUNT" ] || echo "#SBATCH --account=$SLURM_ACCOUNT"
    [ -z "$SLURM_PARTITION" ] || echo "#SBATCH --partition=$SLURM_PARTITION"
    [ -z "$SLURM_GRES" ] || echo "#SBATCH --gres=$SLURM_GRES"
    [ -z "$SLURM_MAIL" ] || printf '#SBATCH --mail-type=ALL\n#SBATCH --mail-user=%s\n' "$SLURM_MAIL"
}

sweep_axes() {  # $1 = model -> grid axes, fastest-varying first (matches the Quest slurm/*_sweep.sh)
    case $1 in
        arousal_mediated) echo "PTRC PCS HOLDOVER" ;;  # no percent_task_in_response axis; holdover swept instead
        *) echo "PTIR PTRC PCS" ;;                      # holdover pinned at 1.0
    esac
}

write_sweep_job() {  # $1 = model -> path of the generated sbatch script
    local model=$1 job=$REPO/slurm/${1}_sweep_$SWEEP_TAG.sh
    {
        sbatch_header "$model"
        cat <<EOF

MODEL=$model
EXPERIMENT=${model}_sweep_$SWEEP_TAG
AXES=($(sweep_axes "$model"))
EOF
        cat <<'EOF'
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

EOF
        echo "\"$VENV/bin/python\" \"$REPO/ratinabox/hsw/main.py\" \"\${ARGS[@]}\""
    } > "$job"
    echo "$job"
}

confirm_submit() {
    local answer=${SUBMIT:-}
    [ -n "$answer" ] || { [ -t 0 ] && read -rp "Submit 3 sweeps x 216 tasks now? [y/N]: " answer; }
    [[ $answer =~ ^[Yy] ]]
}

submit_sweeps() {
    mkdir -p "$REPO/slurm" "$REPO/slurm_out"
    local jobs=() model
    for model in "${MODELS[@]}"; do jobs+=("$(write_sweep_job "$model")"); done
    printf '== Generated ==\n'; printf '  %s\n' "${jobs[@]}"
    confirm_submit || { echo "Not submitted. Submit later with: sbatch <script> for each file above."; return; }
    for job in "${jobs[@]}"; do echo "  $(basename "$job"): job $(sbatch --parsable "$job")"; done
    squeue -u "$USER"
}

REPO=$(find_repo)
CEBRAS_DIR=$(dirname "$REPO")/Hannahs-CEBRAs
collect_settings
clone_cebras "$CEBRAS_DIR"
install_python_env
write_env_file
run_tests
submit_sweeps
echo "Job logs: $REPO/slurm_out/   Results: $SAVE_DIRECTORY/{model}_results/"
