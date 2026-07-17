#!/bin/bash
#SBATCH --account=p32472
#SBATCH --partition=gengpu
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-26  # one task per combination (3 balance x 3 responsive x 3 percent_place_cells)
#SBATCH --mem=8GB
#SBATCH --time=2:00:00
#SBATCH --job-name="holdover_sweep_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=/home/tfl2886/projects/RatInABox/slurm_out/holdover_sweep.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox
PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

# Shared experiment tag so every output file from this sweep shares a prefix.
EXPERIMENT=holdover_sweep

# Fixed config — hold TEBC identity over from env A so task can transfer cross-env,
# and keep the CEBRA config on its tuned defaults so differences are attributable
# to the swept simulation parameters.
MODEL=additive
HOLDOVERS=1
NUM_ITERS=5

# Simulation grid definition — add values here to expand the search
BALANCE_VALUES=(0.25 0.5 0.75)
RESPONSIVE_VALUES=(0.25 0.5 0.75)
PERCENT_PLACE_CELLS=(0.25 0.5 0.75)

# Map task ID to one combination (row-major: balance fastest, then responsive,
# then percent_place_cells)
N_BAL=${#BALANCE_VALUES[@]}
N_RESP=${#RESPONSIVE_VALUES[@]}

IDX=${SLURM_ARRAY_TASK_ID}
BALANCE=${BALANCE_VALUES[$((IDX % N_BAL))]}; IDX=$((IDX / N_BAL))
RESPONSIVE=${RESPONSIVE_VALUES[$((IDX % N_RESP))]}; IDX=$((IDX / N_RESP))
PCS=${PERCENT_PLACE_CELLS[$IDX]}

echo "Task ${SLURM_ARRAY_TASK_ID}: balance=${BALANCE} responsive=${RESPONSIVE} percent_place_cells=${PCS}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
    --model_type "${MODEL}" \
    --experiment "${EXPERIMENT}" \
    --balance_values "${BALANCE}" --balance_dist fixed \
    --responsive_values "${RESPONSIVE}" --responsive_type fixed \
    --percent_place_cells "${PCS}" \
    --holdovers "${HOLDOVERS}" --num_iters "${NUM_ITERS}"
