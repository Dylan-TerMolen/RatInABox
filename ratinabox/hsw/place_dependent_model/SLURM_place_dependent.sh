#!/bin/bash
#SBATCH --account=p32072
#SBATCH --partition=gengpu
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-15  # one task per grid combination (5 percent_task_in_response_values x 1 responsive x 1 pcs)
#SBATCH --mem=8GB
#SBATCH --time=2:00:00
#SBATCH --job-name="PDM_job_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=slurm_out/PDM_SLURM_out.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox
PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

# Grid definition — add values here to expand the search
PERCENT_TASK_IN_RESPONSE_VALUES=(0.0 0.25 0.50 0.75 1.0)
PERCENT_TASK_RESPONSIVE_CELLS_VALUES=(0.50)
PERCENT_PLACE_CELLS=(0.2 0.4 0.6)

# Map task ID to one combination (row-major)
N_PTIR=${#PERCENT_TASK_IN_RESPONSE_VALUES[@]}
N_RESPONSIVE=${#PERCENT_TASK_RESPONSIVE_CELLS_VALUES[@]}

IDX=${SLURM_ARRAY_TASK_ID}
PERCENT_TASK_IN_RESPONSE=${PERCENT_TASK_IN_RESPONSE_VALUES[$((IDX % N_PTIR))]}; IDX=$((IDX / N_PTIR))
PERCENT_TASK_RESPONSIVE_CELLS=${PERCENT_TASK_RESPONSIVE_CELLS_VALUES[$((IDX % N_RESPONSIVE))]}; IDX=$((IDX / N_RESPONSIVE))
PCS=${PERCENT_PLACE_CELLS[$IDX]}

echo "Task ${SLURM_ARRAY_TASK_ID}: percent_task_in_response=${PERCENT_TASK_IN_RESPONSE} responsive=${PERCENT_TASK_RESPONSIVE_CELLS} pcs=${PCS}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
    --model place_dependent \
    --percent_task_in_response_values "${PERCENT_TASK_IN_RESPONSE}" --percent_task_in_response_dist fixed \
    --percent_task_responsive_cells "${PERCENT_TASK_RESPONSIVE_CELLS}" --percent_is_task_responsive_distribution fixed \
    --percent_place_cells "${PCS}" --num_iters 5
