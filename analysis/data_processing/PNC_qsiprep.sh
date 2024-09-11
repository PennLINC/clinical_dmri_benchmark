#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-1397


SIMG="${HOME}"/images/qsiprep-0.21.4.sif
FREESURFER_DIR="${HOME}"/software/freesurfer
SUBJECT_LIST="${HOME}"/clinical_dmri_benchmark/analysis/data_processing/subject_lists/subject_list.txt
DATA_ROOT=/cbica/comp_space/clinical_dmri_benchmark/data/PNC/BIDS
OUTPUTS="${HOME}"/results/qsiprep_outputs

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

# fail whenever something is fishy, use -x to get verbose logfiles
set -e -u -x

# Get the subject id from the call
subid=$(head -n ${SLURM_ARRAY_TASK_ID} ${SUBJECT_LIST} | tail -n 1)

# Use $TMP as the workdir
WORKDIR=${TMP}/"job-${JOB_ID}_${subid}"
mkdir -p "${WORKDIR}"
cd ${WORKDIR}
mkdir -p BIDS

# Copy the files we need from the source directory
cp ${FREESURFER_DIR}/license.txt ./
cp ${DATA_ROOT}/dataset_description.json BIDS/
mkdir -p BIDS/${subid}/ses-PNC1/dwi
mkdir -p BIDS/${subid}/ses-PNC1/anat
cp -r -L ${DATA_ROOT}/${subid}/ses-PNC1/dwi BIDS/${subid}/ses-PNC1/dwi
cp -r -L ${DATA_ROOT}/${subid}/ses-PNC1/anat BIDS/${subid}/ses-PNC1/anat

ls ${WORKDIR}
ls ${WORKDIR}/BIDS
ls ${WORKDIR}/BIDS/${subid}/ses-PNC1/dwi
# Do the run
qsiprep_failed=0
singularity run \
    --containall \
    -B ${PWD} \
    ${SIMG} \
    ${PWD}/BIDS \
    ${PWD}/results \
    participant \
    -w ${PWD}/wkdir \
    --stop-on-first-crash \
    --fs-license-file ${PWD}/license.txt \
    --skip-bids-validation \
    --participant-label "$subid" \
    --output-resolution 1.7 \
    --ignore fieldmaps \
    --separate-all-dwis \
    -v -v \
    --nthreads ${NSLOTS} \
    --omp-nthreads ${NSLOTS} || qsiprep_failed=1      
 
# If qsiprep failed we need to know about it - upload the log to outputs
if [ ${qsiprep_failed} -gt 0 ]; then
    echo QSIPREPFAIL
    FAILS="${OUTPUTS}/failures/${subid}"
    mkdir -p ${FAILS}
    fail_logs=$(find ${PWD}/results -name 'crash*.txt')

    # Copy the failed subject log to the bucket
    mv ${fail_logs} ${FAILS}/crash*.txt

    rm -rf "${WORKDIR}"
    exit 1
fi

# Move results from TMP to project directory
mkdir -p ${OUTPUTS}/${subid}
mv -v ${PWD}/results/qsiprep/${subid}/* ${OUTPUTS}/${subid}/
mv ${PWD}/results/qsiprep/${subid}.html ${OUTPUTS}/${subid}.html
mv ${PWD}/results/qsiprep/dwiqc.json ${OUTPUTS}/dwiqc.json

echo SUCCESSC
