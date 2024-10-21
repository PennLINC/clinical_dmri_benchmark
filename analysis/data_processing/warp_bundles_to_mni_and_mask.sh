#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-1

module load mrtrix/3.0.4
module load gcc
module load ants/2.3.1

SUBJECT_LIST="${HOME}/clinical_dmri_benchmark/subject_lists/subject_list_reconstructed.txt"
MNI_REF_IMG=/cbica/comp_space/clinical_dmri_benchmark/data/MNI/mni_1mm_t1w_lps_brain.nii
ROOT_PREP="${HOME}/results/qsiprep_outputs"
ROOT_RECON="${HOME}/results/qsirecon_outputs"
BUNDLE_NAMES="${HOME}/clinical_dmri_benchmark/data/bundle_names.txt"

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

# Get the subject id from the call
subid=(head -n ${SLURM_ARRAY_TASK_ID} ${SUBJECT_LIST} | tail -n 1)


root_bundles="${ROOT_RECON}/${subid}/ses-PNC1/dwi"
root_bundles_mni="${root_bundles}/mni"
mkdir "${root_bundles_mni}"

path_h5_transform="${ROOT_PREP}/${subid}/anat/${subid}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5"
h5_transform_name_prefix="${subid}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm"

# Create a directory to store the mrtrix transform files and intermediate transforms
root_mrtrix_transform_files="${ROOT_PREP}/${subid}/anat/mrtrix_transform_files"
mkdir "${root_mrtrix_transform_files}"
cd "${root_mrtrix_transform_files}"

# decompose the h5 transformation file into an affine transformation matrix and a warp field image
# 00_<h5_transform_name_prefix>_DisplacementFieldtransform.nii.gz and 01_<h5_transform_name_prefix>_AffineTransform.mat
CompositeTransformUtil --disassemble "${path_h5_transform}" "${h5_transform_name_prefix}"

# A few extra steps need to be performed before applying the transform in mrtrix
# https://community.mrtrix.org/t/registration-using-transformations-generated-from-other-packages/2259

# 1. Initialise warp
warpinit "${MNI_REF_IMG}" "${root_mrtrix_transform_files}/inv_identity_warp[].nii" -force

for run in run-01 run-02;
do
    root_mrtrix_transform_files_run=${root_mrtrix_transform_files}/${run}
    mkdir ${root_mrtrix_transform_files_run}
    path_dwi_image_in=${ROOT_PREP}/${subid}/ses-PNC1/dwi/${subid}_ses-PNC1_${run}_space-T1w_dwiref.nii.gz
    path_affine_transform=${root_mrtrix_transform_files}/01_${h5_transform_name_prefix}_AffineTransform.mat
    path_warp_field=${root_mrtrix_transform_files}/00_${h5_transform_name_prefix}_DisplacementFieldtransform.nii.gz

    # 2. Apply the transformation to identity warp
    for i in {0..2}; do
        antsApplyTransforms -d 3 -e 0 -i ${root_mrtrix_transform_files}/inv_identity_warp${i}.nii -o ${root_mrtrix_transform_files_run}/inv_mrtrix_warp${i}.nii -r ${path_dwi_image_in} -t ${path_affine_transform} -t ${path_warp_field} --default-value 2147483647
    done

    # 3. Fix warp
    warpcorrect ${root_mrtrix_transform_files_run}/inv_mrtrix_warp[].nii ${root_mrtrix_transform_files_run}/inv_mrtrix_warp_corrected.mif -marker 2147483647

    while IFS= read -r bundle;
    do
        path_native_bundle=${root_bundles}/${subid}_ses-PNC1_${run}_space-T1w_desc-preproc_bundle-${bundle}_streamlines.tck
        path_mni_bundle=${root_bundles_mni}/${subid}_ses-PNC1_${run}_space-MNI152NLin2009cAsym_desc-preproc_bundle-${bundle}_streamlines.tck
        # 4. Transform bundle file
        tcktransform ${path_native_bundle} ${root_mrtrix_transform_files_run}/inv_mrtrix_warp_corrected.mif ${path_mni_bundle}

        # 5. calculate binary mask of bundle in MNI space
        path_mni_mask=${root_bundles_mni}/${subid}_ses-PNC1_${run}_space-MNI152NLin2009cAsym_desc-preproc_bundle-${bundle}_mask.nii.gz
        tckmap ${path_mni_bundle} ${path_mni_mask} --template ${MNI_REF_IMG} --contrast tdi
        mrthreshold -force -abs 0 -comparison gt ${path_mni_mask} ${path_mni_mask}
    done < "${BUNDLE_NAMES}"
done