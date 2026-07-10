#!/bin/bash
#SBATCH --account=p32472
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gengpu

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=8GB
#SBATCH --time=1:00:00
#SBATCH --job-name="AM_job_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=/home/tfl2886/projects/RatInABox/slurm_out/all_task_with_no_holdovers.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox

PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

echo "Task ${SLURM_ARRAY_TASK_ID}: balance=${BALANCE} responsive=${RESPONSIVE} pcs=${PCS}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
    --model additive \
    --balance_values "0.51,0.75,0.85,0.95" --balance_dist fixed \
    --responsive_values "0.95" --responsive_type fixed \
    --percent_place_cells "0.51" --num_iters 5 --holdovers 0