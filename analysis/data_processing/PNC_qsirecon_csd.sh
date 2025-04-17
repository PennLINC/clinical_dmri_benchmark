#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=6G
#SBATCH --time=05:00:00
#SBATCH --output=../logs/pnc_odf_recon_CSD-%A_%a.log
#SBATCH --array=1-2

SIMG="${HOME}/images/qsirecon-0.23.2.sif"
FREESURFER_DIR="${HOME}/software/freesurfer"
SUBJECT_LIST="${HOME}/clinical_dmri_benchmark/analysis/data_processing/subject_lists/preprocessed_subject_list_CSD.txt"
DATA_ROOT="/cbica/comp_space/clinical_dmri_benchmark/data/PNC/BIDS"
PREPROCESSED_DATA_ROOT="${HOME}/results/qsiprep_outputs"
OUTPUTS="${HOME}/results/qsirecon_outputs/qsirecon-CSD"
RECON_SPEC="${HOME}/clinical_dmri_benchmark/analysis/data_processing/recon_specs/csd.yaml"
UPDATED_MRTRIX_FILE="${HOME}/clinical_dmri_benchmark/analysis/data_processing/updated_qsirecon_files/mrtrix.py"
UPDATED_BIBTEX_FILE="${HOME}/clinical_dmri_benchmark/analysis/data_processing/updated_qsirecon_files/boilerplate.bib"

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

# Use $TMP as the workdir
WORKDIR="${TMP}/job-${JOB_ID}_${subid}"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
mkdir -p preprocessed_data

# Copy the files we need from the source directory
cp "${FREESURFER_DIR}/license.txt" ./
cp "${RECON_SPEC}" ./
cp "${DATA_ROOT}/dataset_description.json" preprocessed_data/
cp -r "${PREPROCESSED_DATA_ROOT}/${subid}" "preprocessed_data/${subid}"

export TEMPLATEFLOW_HOME=/cbica/projects/clinical_dmri_benchmark/data/TEMPLATEFLOW_HOME

# Do the run
qsirecon_failed=0
singularity run --containall \
    -B "${UPDATED_MRTRIX_FILE}":"/opt/conda/envs/qsiprep/lib/python3.10/site-packages/qsirecon/workflows/recon/mrtrix.py" \
    -B "${UPDATED_BIBTEX_FILE}":"/opt/conda/envs/qsiprep/lib/python3.10/site-packages/qsirecon/data/boilerplate.bib" \
    -B "${PWD}" \
    -B "${TEMPLATEFLOW_HOME}":/templateflow_home \
    --env "TEMPLATEFLOW_HOME=/templateflow_home" \
    "${SIMG}" \
    "${PWD}/preprocessed_data" \
    "${PWD}/results" \
    participant \
    --fs-license-file "${PWD}/license.txt" \
    --recon-spec "${PWD}/csd.yaml" \
    --participant-label "${subid}" \
    --stop-on-first-crash \
    -w "${PWD}/work" \
    -v -v \
    --nthreads ${NSLOTS} \
    --omp-nthreads ${NSLOTS} || qsirecon_failed=1

# If qsirecon failed we need to know about it - upload the log to outputs
if [ "${qsirecon_failed}" -gt 0 ]; then
    echo QSIRECONFAIL
    FAILS="${OUTPUTS}/failures/${subid}"
    mkdir -p "${FAILS}"
    fail_logs=$(find "${PWD}/results" -name 'crash*.txt')

    # Copy the failed subject log to the bucket
    mv "${fail_logs}" "${FAILS}/crash*.txt"

    rm -rf "${WORKDIR}"
    exit 1
fi

# Move results from TMP to project directory
mkdir -p "${OUTPUTS}/${subid}"
mv -v "${PWD}/results/derivatives/qsirecon-CSD/${subid}"/* "${OUTPUTS}/${subid}/"
mv "${PWD}/results/derivatives/qsirecon-CSD/${subid}.html" "${OUTPUTS}/${subid}.html"
echo SUCCESS
