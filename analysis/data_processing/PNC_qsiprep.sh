#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=32G
#SBATCH --time=10:00:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-1397


SIMG="${HOME}"/images/qsiprep-0.21.4.sif
CODE_DIR="${HOME}"/clinical_dmri_benchmark/code
SUBJECT_LIST="${HOME}"/clinical_dmri_benchmark/analysis/data_processing/subject_lists/subject_list.txt
DATA_ROOT="/cbica/comp_space/clinical_dmri_benchmark/data/PNC/"
OUTPUTS="${HOME}/results/qsiprep_outputs"

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

# Use $TMP as the workdir
WORKDIR=${TMP}/"job-${JOB_ID}_${subid}_${sesid}"
mkdir -p "${WORKDIR}"
cd ${WORKDIR}

# Copy the files we need from the source directory
cp ${CODE_DIR}/license.txt ./
cp ${CODE_DIR}/dataset_description.json BIDS/
cp -r ${DATA_ROOT}/${subid} BIDS/${subid}

# Do the run
qsiprep_failed=0
singularity run \
    --containall \
    -B ${PWD} \
    ${SIMG} \
    ${DATA_ROOT} \
    ${PWD}/results \
    participant \
    -w ${PWD}/wkdir \
    --stop-on-first-crash \
    --fs-license-file ${PWD}/license.txt \
    --skip-bids-validation \
    --participant-label "$subid" \
    --unringing-method rpg \
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
    fail_logs=$(find results -name 'crash*.txt')

    # Copy the failed subject log to the bucket
    mv $fail_logs ${FAILS}/

    rm -rf "${WORKDIR}"
    exit 1
fi

# Move results from TMP to project directory
mv -v ${PWD}/results/qsiprep/${subid}/* ${OUTPUTS}/${subid}/
mv ${PWD}/results/qsiprep/${subid}.html ${OUTPUTS}/${subid}.html
mv ${PWD}/results/qsiprep/dwiqc.json ${OUTPUTS}/dwiqc.json

echo SUCCESS