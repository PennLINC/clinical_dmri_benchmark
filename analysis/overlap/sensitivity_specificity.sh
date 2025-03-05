#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=5G
#SBATCH --time=08:00:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-1

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

RECON_SUFFIX=$1
PYTHON_HELPER_SCRIPT="/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/overlap/sensitivity_specificity.py"

source /cbica/projects/clinical_dmri_benchmark/micromamba/etc/profile.d/micromamba.sh

micromamba activate clinical_dmri_benchmark

python3 ${PYTHON_HELPER_SCRIPT} ${RECON_SUFFIX}

micromamba deactivate

echo SUCCESS

