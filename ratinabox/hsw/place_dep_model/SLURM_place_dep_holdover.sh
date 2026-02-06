#!/bin/bash
#SBATCH --account=p32072
#SBATCH --partition=gengpu
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --array=0 ## number of jobs to run "in parallel"
#SBATCH --mem=220GB
#SBATCH --time=24:00:00
#SBATCH --job-name="sample_job_\${SLURM_ARRAY_TASK_ID}" ## use the task id in the name of the job
#SBATCH --output=PDM_SLURM_out.%A_%a.out ## use the jobid (A) and the specific job index (a) to name your log file
#SBATCH --mail-type=ALL ## you can receive e-mail alerts from SLURM when your job begins and when your job finishes (completed, failed, etc)
#SBATCH --mail-user=hsw@northwestern.edu  ## your email


module purge
eval "$(conda shell.bash hook)"
source activate ratinabox

export PYTHONPATH="${PYTHONPATH}:/home/hsw967/Programming/RatInABox"
export PYTHONPATH="${PYTHONPATH}:/home/hsw967/Programming/Hannahs-CEBRAs"

# Run the Python script with hardcoded arguments
#python /home/hsw967/Programming/RatInABox/HSW/place_dep_model/main2.py --responsive_values 0,.2,.4,.6,.8,1 --responsive_type fixed --percent_place_cells 0,.2,.4,.6,.8,1 --holdovers 1 --num_iters 5 --optional_param work
python /home/hsw967/Programming/RatInABox/HSW/place_dep_model/main2.py --responsive_values 0,.10,.20,.30,.40 --responsive_type fixed --percent_place_cells 0,.10,.20,.30,.40 --holdovers 1 --num_iters 5 --optional_param work
