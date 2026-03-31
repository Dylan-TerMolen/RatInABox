#!/bin/bash
#SBATCH --account=p32472
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gengpu

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-2  # one task per grid combination (3 responsive_values x 1 pcs)
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
RESPONSIVE_VALUES=(0.25 0.50 0.75)
PERCENT_PLACE_CELLS=(0.50)

# Map task ID to one combination (row-major)
N_RESPONSIVE=${#RESPONSIVE_VALUES[@]}

IDX=${SLURM_ARRAY_TASK_ID}
RESPONSIVE=${RESPONSIVE_VALUES[$((IDX % N_RESPONSIVE))]}; IDX=$((IDX / N_RESPONSIVE))
PCS=${PERCENT_PLACE_CELLS[$IDX]}

echo "Task ${SLURM_ARRAY_TASK_ID}: responsive=${RESPONSIVE} pcs=${PCS}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
      --model place_dependent \
      --responsive_values "${RESPONSIVE}" --responsive_type fixed \
      --percent_place_cells "${PCS}" --holdovers 1 --num_iters 5


    