#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=5G
#SBATCH --time=01:00:00
#SBATCH --output=../logs/pnc_warp_mnib2c-%A_%a.log
#SBATCH --array=1-1

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

PYTHON_HELPER_SCRIPT="${HOME}/clinical_dmri_benchmark/analysis/overlap/calculate_transform_mnib2c.py"
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=$SLURM_CPUS_PER_TASK

source /cbica/projects/clinical_dmri_benchmark/micromamba/etc/profile.d/micromamba.sh

micromamba activate clinical_dmri_benchmark

python3 ${PYTHON_HELPER_SCRIPT}

micromamba deactivate

echo SUCCESS
