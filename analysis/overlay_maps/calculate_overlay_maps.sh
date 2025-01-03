#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=5G
#SBATCH --time=01:00:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-60

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

BUNDLE_LIST="${HOME}/clinical_dmri_benchmark/data/bundle_names.txt"
# Get the subject id from the call
bundle=$(head -n "${SLURM_ARRAY_TASK_ID}" "${BUNDLE_LIST}" | tail -n 1)
bundle="${bundle//[_-]/}"

RECON_SUFFIX=$1
PYTHON_HELPER_SCRIPT="${HOME}/clinical_dmri_benchmark/analysis/overlay_maps/calculate_overlay_maps.py"

source /cbica/projects/clinical_dmri_benchmark/micromamba/etc/profile.d/micromamba.sh

micromamba activate clinical_dmri_benchmark

python3 ${PYTHON_HELPER_SCRIPT} --recon_suffix ${RECON_SUFFIX} --bundle ${bundle}

micromamba deactivate

echo SUCCESS
