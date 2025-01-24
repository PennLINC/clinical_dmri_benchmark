#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=01:30:00
#SBATCH --output=/cbica/projects/abcd_qsiprep/bundle_comparison/logs/MNIWarp-%A_%a.log
#SBATCH --array=1-1 #940

# The recon_suffix is passed as the first positional argument such that the script can be used for different reconstruction methods

SUBJECT_LIST="${HOME}/bundle_comparison/clinical_dmri_benchmark/analysis/data_processing/subject_lists/reconstructed_subject_list_${RECON_SUFFIX}.txt"

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

# Get the subject id from the call
#subid=$(head -n "${SLURM_ARRAY_TASK_ID}" "${SUBJECT_LIST}" | tail -n 1)
subid_root="00CY2MDM" # TMP FOR TESTING

HELPER_SCRIPT="${HOME}/bundle_comparison/clinical_dmri_benchmark/analysis/data_processing/warp_bundles_to_mni_and_mask_helper.sh"
MNI_REF_IMG=${HOME}/bundle_comparison/mni_1mm_t1w_lps_brain.nii
BUNDLE_NAMES="${HOME}/bundle_comparison/clinical_dmri_benchmark/data/bundle_names.txt"

for RECON_SUFFIX in "GQIAutoTrack"  "MSMTAutoTrack"  "SS3TAutoTrack"; do
for SESSION in "ses-baselineYear1Arm1" "ses-2YearFollowUpYArm1" "ses-04A" "ses-06A"; do

# If session is baseline or year 2, then subid = sub-NDARINV{subid_root}
if [[ "${SESSION}" == "ses-baselineYear1Arm1" || "${SESSION}" == "ses-2YearFollowUpYArm1" ]]; then
    subid="sub-NDARINV${subid_root}"
else
    subid="sub-${subid_root}"
fi

ROOT_PREP_SES="${HOME}/bundle_comparison/test_data/qsiprep/${subid}/${SESSION}/"
ROOT_RECON_SES="${HOME}/bundle_comparison/test_data/qsirecon-${RECON_SUFFIX}/${subid}/${SESSION}/"
ROOT_BUNDLES="${ROOT_RECON_SES}/dwi"

singularity exec --env SESSION="${SESSION}"  --containall -B "${ROOT_BUNDLES}":/root_bundles \
    -B "${HOME}/bundle_comparison/clinical_dmri_benchmark/analysis/data_processing":/img \
    -B "${ROOT_PREP_SES}":/root_prep \
    -B "${MNI_REF_IMG}":/mni/ref_image.nii \
    -B "${BUNDLE_NAMES}":/data/bundle_names.txt \
    "${HOME}/s3qsiprep/images/qsirecon-1.0.0rc2.sif" \
    /bin/bash /img/warp_bundles_to_mni_and_mask_helper.sh "${subid}"

done
done
