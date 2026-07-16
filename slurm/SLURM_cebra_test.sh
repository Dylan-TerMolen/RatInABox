#!/bin/bash
#SBATCH --account=p32072
#SBATCH --partition=gengpu
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=8GB
#SBATCH --time=2:00:00
#SBATCH --job-name="CEBRA_test"
#SBATCH --output=/home/tfl2886/projects/RatInABox/slurm_out/CEBRA_test.%j.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox
PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

# Fixed simulation config for the CEBRA wiring test
MODEL=dependent
BALANCE_VALUE=0.75
RESPONSIVE_VALUE=0.75
PERCENT_PLACE_CELLS=0.5
HOLDOVERS=0
NUM_ITERS=1

# CEBRA parameters under test — every value here is recorded in the run's .log header
CEBRA_LEARNING_RATE=3e-4
CEBRA_MAX_ITERATIONS=5000
CEBRA_OUTPUT_DIMENSION=3
CEBRA_MIN_TEMPERATURE=0.3

echo "CEBRA test: lr=${CEBRA_LEARNING_RATE} max_iter=${CEBRA_MAX_ITERATIONS} dim=${CEBRA_OUTPUT_DIMENSION} min_temp=${CEBRA_MIN_TEMPERATURE}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
    --model_type "${MODEL}" \
    --balance_values "${BALANCE_VALUE}" --balance_dist fixed \
    --responsive_values "${RESPONSIVE_VALUE}" --responsive_type fixed \
    --percent_place_cells "${PERCENT_PLACE_CELLS}" \
    --holdovers "${HOLDOVERS}" --num_iters "${NUM_ITERS}" \
    --cebra_learning_rate "${CEBRA_LEARNING_RATE}" \
    --cebra_max_iterations "${CEBRA_MAX_ITERATIONS}" \
    --cebra_output_dimension "${CEBRA_OUTPUT_DIMENSION}" \
    --cebra_min_temperature "${CEBRA_MIN_TEMPERATURE}"
