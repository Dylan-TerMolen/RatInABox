#!/bin/bash
#SBATCH --account=p32472
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gengpu

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-1 ## number of jobs to run "in parallel"
#SBATCH --mem=220GB
#SBATCH --time=24:00:00
#SBATCH --job-name="SL_job_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=slurm_out/SL_SLURM_out.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox
PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/separate_learning/main.py" \
    --balance_values 0,.10,.20,.30,.40 --balance_dist fixed \
    --responsive_values 0,.10,.20,.30,.40 --responsive_type fixed
