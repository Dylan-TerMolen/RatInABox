#!/bin/bash
#SBATCH --account=p32472
#SBATCH --partition=gengpu
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-29  # one task per CEBRA grid combination (5 learning_rate x 3 output_dimension x 2 min_temperature)
#SBATCH --mem=8GB
#SBATCH --time=1:30:00
#SBATCH --job-name="CEBRA_search_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=/home/tfl2886/projects/RatInABox/slurm_out/CEBRA_search.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox
PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

# Fixed simulation config (holds the neural population constant so differences
# in decoding are attributable to the CEBRA hyperparameters, not the data).
MODEL=additive
BALANCE_VALUE=0.75
RESPONSIVE_VALUE=0.75
PERCENT_PLACE_CELLS=0.5
HOLDOVERS=0
NUM_ITERS=5

# Isolate the task decoder: a single --cebra_learning_rate overrides both decoders,
# and only task can transfer cross-env (place cells always remap), so we sweep the
# task decoder alone to keep every grid point interpretable.
DECODE_POSITION=false

# CEBRA grid definition — add values here to expand the search
LEARNING_RATES=(5e-5 1e-4 3e-4 8.6e-4 2e-3)
OUTPUT_DIMENSIONS=(2 4 8)
MIN_TEMPERATURES=(0.1 0.5)

# Map task ID to one combination (row-major: learning_rate fastest, then
# output_dimension, then min_temperature)
N_LR=${#LEARNING_RATES[@]}
N_DIM=${#OUTPUT_DIMENSIONS[@]}

IDX=${SLURM_ARRAY_TASK_ID}
LR=${LEARNING_RATES[$((IDX % N_LR))]}; IDX=$((IDX / N_LR))
DIM=${OUTPUT_DIMENSIONS[$((IDX % N_DIM))]}; IDX=$((IDX / N_DIM))
TEMP=${MIN_TEMPERATURES[$IDX]}

echo "Task ${SLURM_ARRAY_TASK_ID}: cebra_learning_rate=${LR} cebra_output_dimension=${DIM} cebra_min_temperature=${TEMP}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
    --model_type "${MODEL}" \
    --balance_values "${BALANCE_VALUE}" --balance_dist fixed \
    --responsive_values "${RESPONSIVE_VALUE}" --responsive_type fixed \
    --percent_place_cells "${PERCENT_PLACE_CELLS}" \
    --holdovers "${HOLDOVERS}" --num_iters "${NUM_ITERS}" \
    --decode_position "${DECODE_POSITION}" \
    --cebra_learning_rate "${LR}" \
    --cebra_output_dimension "${DIM}" \
    --cebra_min_temperature "${TEMP}"
