#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=3G
#SBATCH --time=02:00:00
#SBATCH --output=../logs/pnc-%A_%a.log

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

RECON_SUFFIX_1=$1
RECON_SUFFIX_2=$2
RECON_SUFFIX_3=$3
PYTHON_HELPER_SCRIPT="${HOME}/clinical_dmri_benchmark/analysis/discriminability/discrim_two_sample_filtered.py"

source /cbica/projects/clinical_dmri_benchmark/micromamba/etc/profile.d/micromamba.sh

micromamba activate clinical_dmri_benchmark

python3 ${PYTHON_HELPER_SCRIPT} --recon_suffix_1 ${RECON_SUFFIX_1} --recon_suffix_2 ${RECON_SUFFIX_2} --recon_suffix_3 ${RECON_SUFFIX_3} --workers ${SLURM_JOB_CPUS_PER_NODE}

micromamba deactivate

echo SUCCESS
