set -e -u -x
SUBID="${1}"
ROOT_BUNDLES_MNI=/root_bundles/MNI
mkdir -p "${ROOT_BUNDLES_MNI}"

PATH_H5_TRANSFORM="/root_prep/anat/${SUBID}_${SESSION}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5"
H5_TRANSFORM_NAME_PREFIX="${SUBID}_${SESSION}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm"

# Create a directory to store the mrtrix transform files and intermediate transforms
ROOT_MRTRIX_TRANSFORM_FILES="/root_prep/anat/mrtrix_transform_files"
mkdir -p "${ROOT_MRTRIX_TRANSFORM_FILES}"
cd "${ROOT_MRTRIX_TRANSFORM_FILES}"

# decompose the h5 transformation file into an affine transformation matrix and a warp field image
# 00_<h5_transform_name_prefix>_DisplacementFieldtransform.nii.gz and 01_<h5_transform_name_prefix>_AffineTransf$
CompositeTransformUtil --disassemble \
    "${PATH_H5_TRANSFORM}" \
    "${H5_TRANSFORM_NAME_PREFIX}"

# A few extra steps need to be performed before applying the transform in mrtrix
# https://community.mrtrix.org/t/registration-using-transformations-generated-from-other-packages/2259

# 1. Initialise warp
warpinit /mni/ref_image.nii "${ROOT_MRTRIX_TRANSFORM_FILES}"/inv_identity_warp[].nii -force

ROOT_MRTRIX_TRANSFORM_FILES_RUN="${ROOT_MRTRIX_TRANSFORM_FILES}/"
mkdir -p ${ROOT_MRTRIX_TRANSFORM_FILES_RUN}
source_file=$(ls /root_prep/dwi/${SUBID}_${SESSION}*_space-T1w_dwiref.nii.gz  2> /dev/null)
file_name=$(basename "$source_file")
file_name_prefix="${file_name%%_space-T1w_*}_space"
PATH_DWI_IMAGE_IN="/root_prep/dwi/${file_name_prefix}-T1w_dwiref.nii.gz"
PATH_AFFINE_TRANSFORM=${ROOT_MRTRIX_TRANSFORM_FILES}/01_${H5_TRANSFORM_NAME_PREFIX}_AffineTransform.mat
PATH_WARP_FIELD=${ROOT_MRTRIX_TRANSFORM_FILES}/00_${H5_TRANSFORM_NAME_PREFIX}_DisplacementFieldtransform.nii.gz

# 2. Apply the transformation to identity warp
for i in {0..2}; do
    antsApplyTransforms -d 3 -e 0 -i "${ROOT_MRTRIX_TRANSFORM_FILES}/inv_identity_warp${i}.nii" \
    -o "${ROOT_MRTRIX_TRANSFORM_FILES_RUN}/inv_mrtrix_warp${i}.nii" \
    -r "${source_file}" \
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
    bundle_path=/root_bundles/${SUBID}_${SESSION}_space-T1w_model-*_bundle-${BUNDLE}_streamlines.tck.gz
    if compgen -G "${bundle_path}" > /dev/null; then
        PATH_NATIVE_BUNDLE=$(ls ${bundle_path})
        file_name=$(basename "$PATH_NATIVE_BUNDLE")
        # Replace 'space-T1w' with 'space-MNI152NLin2009cAsym' in the filename
        file_name_mni=$(echo "$file_name" | sed 's/space-T1w/space-MNI152NLin2009cAsym/')
        PATH_MNI_BUNDLE="${ROOT_BUNDLES_MNI}/${file_name_mni%.gz}"

        gunzip -f "${PATH_NATIVE_BUNDLE}"
        # 4. Transform bundle file
        tcktransform "/root_bundles/${file_name%.gz}" \
        "${ROOT_MRTRIX_TRANSFORM_FILES_RUN}/inv_mrtrix_warp_corrected.mif" \
        "${PATH_MNI_BUNDLE}" -force

        gzip "/root_bundles/${file_name%.gz}"

        # 5. calculate binary mask of bundle in MNI space
        # mask_name = MNI_BUNDLE PATH but with _mask.nii ending
        mni_mask_name=$(echo "${PATH_MNI_BUNDLE}" | sed 's/_streamlines.tck\(.\gz\)*$/_mask.nii.gz/')
	tckmap "${PATH_MNI_BUNDLE}" --template /mni/ref_image.nii --contrast tdi -force "${mni_mask_name}"


        mrthreshold -abs 0 -comparison gt "${mni_mask_name}" \
        "${mni_mask_name}" -force

        # gzip "${PATH_MNI_BUNDLE}"
	rm "${PATH_MNI_BUNDLE}"
        gzip "${mni_mask_name}"

        else
            echo "File ${bundle_path} does not exist, skipping."
            continue
        fi
done
