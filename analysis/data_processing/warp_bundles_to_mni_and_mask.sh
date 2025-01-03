#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=01:30:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-1397

# The recon_suffix is passed as the first positional argument such that the script can be used for different reconstruction methods
RECON_SUFFIX="${1}"
SUBJECT_LIST="${HOME}/clinical_dmri_benchmark/analysis/data_processing/subject_lists/reconstructed_subject_list_${RECON_SUFFIX}.txt"

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

# Get the subject id from the call
subid=$(head -n "${SLURM_ARRAY_TASK_ID}" "${SUBJECT_LIST}" | tail -n 1)

MNI_REF_IMG=/cbica/comp_space/clinical_dmri_benchmark/data/MNI/mni_1mm_t1w_lps_brain.nii
ROOT_PREP="${HOME}/results/qsiprep_outputs/${subid}"
ROOT_RECON="${HOME}/results/qsirecon_outputs/qsirecon-${RECON_SUFFIX}"
BUNDLE_NAMES="${HOME}/clinical_dmri_benchmark/data/bundle_names.txt"
HELPER_SCRIPT="${HOME}/clinical_dmri_benchmark/analysis/data_processing/warp_bundles_to_mni_and_mask_helper.sh"


ROOT_BUNDLES="${ROOT_RECON}/${subid}/ses-PNC1/dwi"

singularity exec --containall -B "${ROOT_BUNDLES}":/root_bundles \
    -B "${HOME}/clinical_dmri_benchmark/analysis/data_processing":/img \
    -B "${ROOT_PREP}":/root_prep \
    -B "${MNI_REF_IMG}":/mni/ref_image.nii \
    -B "${BUNDLE_NAMES}":/data/bundle_names.txt \
    "${HOME}/images/qsirecon-0.23.2.sif" \
    /bin/bash /img/warp_bundles_to_mni_and_mask_helper.sh "${subid}"

