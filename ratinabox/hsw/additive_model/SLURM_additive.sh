#!/bin/bash
#SBATCH --account=p32472
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gengpu

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-4  # one task per grid combination (5 balance_values x 1 responsive x 1 pcs)
#SBATCH --mem=8GB
#SBATCH --time=2:00:00
#SBATCH --job-name="AM_job_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=slurm_out/AM_SLURM_out.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox

PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

# Grid definition — add values here to expand the search
BALANCE_VALUES=(0.0 0.25 0.50 0.75 1.0)
RESPONSIVE_VALUES=(0.50)
PERCENT_PLACE_CELLS=(0.50)

# Map task ID to one combination (row-major)
N_BALANCE=${#BALANCE_VALUES[@]}
N_RESPONSIVE=${#RESPONSIVE_VALUES[@]}

IDX=${SLURM_ARRAY_TASK_ID}
BALANCE=${BALANCE_VALUES[$((IDX % N_BALANCE))]}; IDX=$((IDX / N_BALANCE))
RESPONSIVE=${RESPONSIVE_VALUES[$((IDX % N_RESPONSIVE))]}; IDX=$((IDX / N_RESPONSIVE))
PCS=${PERCENT_PLACE_CELLS[$IDX]}

echo "Task ${SLURM_ARRAY_TASK_ID}: balance=${BALANCE} responsive=${RESPONSIVE} pcs=${PCS}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
    --model additive \
    --balance_values "${BALANCE}" --balance_dist fixed \
    --responsive_values "${RESPONSIVE}" --responsive_type fixed \
    --percent_place_cells "${PCS}" --num_iters 5