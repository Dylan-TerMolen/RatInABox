#!/bin/bash
#SBATCH --account=p32472
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gengpu

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0 ## number of jobs to run "in parallel"
#SBATCH --mem=220GB
#SBATCH --time=48:00:00
#SBATCH --job-name="PDM_job_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=slurm_out/PDM_SLURM_out.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox
PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

"${PYTHON}" "${BASE_DIR}/ratinabox/hsw/place_dep_model/main2.py" \
      --responsive_values 0.25,0.50,0.75 --responsive_type fixed \
      --percent_place_cells 0.25,0.50,0.75 --holdover 1 --num_iters 1


    