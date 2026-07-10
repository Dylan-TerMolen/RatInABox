#!/bin/bash
#SBATCH --account=p32072
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gengpu

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0-1
#SBATCH --mem=8GB
#SBATCH --time=2:00:00
#SBATCH --job-name="TEST_job_${SLURM_ARRAY_TASK_ID}"
#SBATCH --output=slurm_out/TEST_SLURM_out.%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dptermolen@gmail.com

BASE_DIR=/home/tfl2886/projects/RatInABox
PYTHON=${HOME}/miniconda3/envs/ratinabox/bin/python

module purge

# Task 0: additive, balance=0.5, pcs=0.5, no holdovers
# Task 1: additive, balance=0.5, pcs=0.5, holdovers

case ${SLURM_ARRAY_TASK_ID} in
    0)
        echo "Task 0: additive model, balance=0.5, pcs=0.5, holdovers=0"
        "${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
            --model_type additive \
            --balance_values 0.5 --balance_dist fixed \
            --responsive_values 0.5 --responsive_type fixed \
            --percent_place_cells 0.5 --holdovers 0 --num_iters 5
        ;;
    1)
        echo "Task 1: additive model, balance=0.6, pcs=0.5, holdovers=1"
        "${PYTHON}" "${BASE_DIR}/ratinabox/hsw/main.py" \
            --model_type additive \
            --balance_values 0.5 --balance_dist fixed \
            --responsive_values 0.5 --responsive_type fixed \
            --percent_place_cells 0.5 --holdovers 1 --num_iters 5
        ;;
esac
