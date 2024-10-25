#!/bin/bash

# the subject ID will be passed to this script as argument
SUBID="${1}"
ROOT_BUNDLES_MNI=/root_bundles/MNI
mkdir -p "${ROOT_BUNDLES_MNI}"

PATH_H5_TRANSFORM="/root_prep/${SUBID}/anat/${SUBID}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5"
H5_TRANSFORM_NAME_PREFIX="${SUBID}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm"

# Create a directory to store the mrtrix transform files and intermediate transforms
ROOT_MRTRIX_TRANSFORM_FILES="/root_prep/${SUBID}/anat/mrtrix_transform_files"
mkdir -p "${ROOT_MRTRIX_TRANSFORM_FILES}"
cd "${ROOT_MRTRIX_TRANSFORM_FILES}"

# decompose the h5 transformation file into an affine transformation matrix and a warp field image
# 00_<h5_transform_name_prefix>_DisplacementFieldtransform.nii.gz and 01_<h5_transform_name_prefix>_AffineTransform.mat
CompositeTransformUtil --disassemble \
    "${PATH_H5_TRANSFORM}" \
    "${H5_TRANSFORM_NAME_PREFIX}"

# A few extra steps need to be performed before applying the transform in mrtrix
# https://community.mrtrix.org/t/registration-using-transformations-generated-from-other-packages/2259

# 1. Initialise warp
warpinit /mni/ref_image.nii "${ROOT_MRTRIX_TRANSFORM_FILES}"/inv_identity_warp[].nii -force

for run in run-01 run-02;
do
    ROOT_MRTRIX_TRANSFORM_FILES_RUN="${ROOT_MRTRIX_TRANSFORM_FILES}/${run}"
    mkdir -p ${ROOT_MRTRIX_TRANSFORM_FILES_RUN}
    PATH_DWI_IMAGE_IN="/root_prep/${SUBID}/ses-PNC1/dwi/${SUBID}_ses-PNC1_${run}_space-T1w_dwiref.nii.gz"
    PATH_AFFINE_TRANSFORM=${ROOT_MRTRIX_TRANSFORM_FILES}/01_${H5_TRANSFORM_NAME_PREFIX}_AffineTransform.mat
    PATH_WARP_FIELD=${ROOT_MRTRIX_TRANSFORM_FILES}/00_${H5_TRANSFORM_NAME_PREFIX}_DisplacementFieldtransform.nii.gz

    # 2. Apply the transformation to identity warp
    for i in {0..2}; do
        antsApplyTransforms -d 3 -e 0 -i "${ROOT_MRTRIX_TRANSFORM_FILES}/inv_identity_warp${i}.nii" \
        -o "${ROOT_MRTRIX_TRANSFORM_FILES_RUN}/inv_mrtrix_warp${i}.nii" \
        -r "${PATH_DWI_IMAGE_IN}" \
        -t "${ROOT_MRTRIX_TRANSFORM_FILES}/01_${H5_TRANSFORM_NAME_PREFIX}_AffineTransform.mat" \
        -t "${ROOT_MRTRIX_TRANSFORM_FILES}/00_${H5_TRANSFORM_NAME_PREFIX}_DisplacementFieldTransform.nii.gz" \
        --default-value 2147483647
    done

    # 3. Fix warp
    warpcorrect "${ROOT_MRTRIX_TRANSFORM_FILES_RUN}/inv_mrtrix_warp[].nii" \
    "${ROOT_MRTRIX_TRANSFORM_FILES_RUN}/inv_mrtrix_warp_corrected.mif" \
    -marker 2147483647 -force

    # Iterate over all bundles to warp them to MNI space and calculate a 3D mask
    mapfile -t bundle_array < /data/bundle_names.txt
    for bundle in "${bundle_array[@]}";
    do
        BUNDLE=${bundle//[_-]/}
        PATH_NATIVE_BUNDLE="/root_bundles/${SUBID}_ses-PNC1_${run}_space-T1w_bundle-${BUNDLE}_streamlines.tck.gz"
        if [ ! -f "${PATH_NATIVE_BUNDLE}" ]; then
            echo "File ${PATH_NATIVE_BUNDLE} does not exist, skipping."
            continue
        fi
        PATH_MNI_BUNDLE="${ROOT_BUNDLES_MNI}/${SUBID}_ses-PNC1_${run}_space-MNI152NLin2009cAsym_bundle-${BUNDLE}_streamlines.tck"
        
        gunzip "${PATH_NATIVE_BUNDLE}"
        4. Transform bundle file
        tcktransform "/root_bundles/${SUBID}_ses-PNC1_${run}_space-T1w_bundle-${BUNDLE}_streamlines.tck" \
        "${ROOT_MRTRIX_TRANSFORM_FILES_RUN}/inv_mrtrix_warp_corrected.mif" \
        "${PATH_MNI_BUNDLE}" -force

        gzip "/root_bundles/${SUBID}_ses-PNC1_${run}_space-T1w_bundle-${BUNDLE}_streamlines.tck"

        # 5. calculate binary mask of bundle in MNI space
        tckmap "${PATH_MNI_BUNDLE}" "${ROOT_BUNDLES_MNI}/${SUBID}_ses-PNC1_${run}_space-MNI152NLin2009cAsym_bundle-${BUNDLE}_mask.nii" --template /mni/ref_image.nii --contrast tdi -force

        mrthreshold -abs 0 -comparison gt "${ROOT_BUNDLES_MNI}/${SUBID}_ses-PNC1_${run}_space-MNI152NLin2009cAsym_bundle-${BUNDLE}_mask.nii" \
        "${ROOT_BUNDLES_MNI}/${SUBID}_ses-PNC1_${run}_space-MNI152NLin2009cAsym_bundle-${BUNDLE}_mask.nii" -force

        gzip "${PATH_MNI_BUNDLE}"
        gzip "${ROOT_BUNDLES_MNI}/${SUBID}_ses-PNC1_${run}_space-MNI152NLin2009cAsym_bundle-${BUNDLE}_mask.nii"
    done
done
