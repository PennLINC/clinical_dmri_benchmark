#!/bin/bash

BUNDLE_NAMES="${HOME}/clinical_dmri_benchmark/data/bundle_names.txt"
TEMPLATE="${HOME}/data/HCP1065.1mm.fib.gz"
ROOT_BUNDLES="${HOME}/data/atlas_bundles"
ROOT_MASKS="${HOME}/data/atlas_bundles"
TRANSFORM="${HOME}/data/atlas_bundles/anat_nlin_normalization/ants_t1_to_mniComposite.h5"
REFERENCE="${HOME}/results/overlay_maps/CSDautotrack/AssociationArcuateFasciculusL.nii.gz"

mkdir -p ${ROOT_MASKS}

mapfile -t bundle_array < ${BUNDLE_NAMES}
for bundle in "${bundle_array[@]}";
do
  echo ${bundle}
    # Calculate mask from streamlines
  singularity exec --containall -B "${ROOT_BUNDLES}":/root_bundles \
      -B "${ROOT_MASKS}":/root_masks \
      -B "${TEMPLATE}":/tmp/hcp_template.fib.gz \
      "${HOME}/images/qsirecon-0.23.2.sif" \
      dsi_studio --action=ana --source=/tmp/hcp_template.fib.gz --tract=/root_bundles/${bundle}.tt.gz --output=/root_masks/${bundle}.nii.gz
  # Warp mask from MNIb to MNIc space
  singularity exec --containall -B "${ROOT_MASKS}":/root_masks \
    -B "${REFERENCE}":/tmp/reference.nii.gz \
    -B "${TRANSFORM}":/tmp/transform.h5 \
    "${HOME}/images/qsirecon-0.23.2.sif" \
    antsApplyTransforms -d 3 -i /root_masks/${bundle}.nii.gz -r /tmp/reference.nii.gz -o /root_masks/${bundle}_MNIc.nii.gz -n NearestNeighbor -t /tmp/transform.h5
done