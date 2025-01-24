#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=5G
#SBATCH --time=05:00:00
#SBATCH --output=/cbica/projects/abcd_qsiprep/bundle_comparison/logs/MNIWarp-%A_%a.log
#SBATCH --array=1-60

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

BUNDLE_LIST="${HOME}/bundle_comparison/clinical_dmri_benchmark/data/bundle_names.txt"
# Get the subject id from the call
#bundle=$(head -n "${SLURM_ARRAY_TASK_ID}" "${BUNDLE_LIST}" | tail -n 1)
bundle="Association_ArcuateFasciculusL"
bundle="${bundle//[_-]/}"

PYTHON_HELPER_SCRIPT="${HOME}/bundle_comparison/clinical_dmri_benchmark/analysis/dice_scores/calculate_dice_scores.py"

source ${HOME}/miniconda3/etc/profile.d/conda.sh

conda activate bundlestats

for RECON_SUFFIX in "GQIAutoTrack"  "MSMTAutoTrack"  "SS3TAutoTrack"; do
    python3 ${PYTHON_HELPER_SCRIPT} --recon_suffix ${RECON_SUFFIX} --bundle ${bundle}
done

conda deactivate

echo SUCCESS
