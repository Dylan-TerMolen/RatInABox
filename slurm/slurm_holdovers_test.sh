#!/bin/bash
#SBATCH --account=p32472
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gengpu

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=8GB
#SBATCH --time=1:00:00
#SBATCH --job-name="AM_job_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=slurm_out/AM_SLURM_out.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox

PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

echo "Task ${SLURM_ARRAY_TASK_ID}: balance=${BALANCE} responsive=${RESPONSIVE} pcs=${PCS}"

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
    --model additive \
    --balance_values "0.52" --balance_dist fixed \
    --responsive_values "0.52" --responsive_type fixed \
    --percent_place_cells "0.52" --num_iters 5 --holdovers 1