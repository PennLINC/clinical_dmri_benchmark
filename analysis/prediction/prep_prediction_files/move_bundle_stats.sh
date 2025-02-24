# This script moves the bundle stats files from their subfolders in the recon_output to one folder
# for easier processing.
# Run with arguments GQIautotrack, CSDautotrack or SS3Tautotrack.
BASE_DIR=/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/qsirecon-${1}
BASE_DIR_OUTPUT=/cbica/projects/clinical_dmri_benchmark/results/bundle_stats/${1}
if [ ! -d ${BASE_DIR_OUTPUT} ]; then
  mkdir -p ${BASE_DIR_OUTPUT}
fi

for folder in "${BASE_DIR}"/*/; do
  subject_id=$(basename "$folder")
 echo "${subject_id}"
 cp ${BASE_DIR}/${subject_id}/ses-PNC1/dwi/*_bundlestats.csv ${BASE_DIR_OUTPUT}/
done
