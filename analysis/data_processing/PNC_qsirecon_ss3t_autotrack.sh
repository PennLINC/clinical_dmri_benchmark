#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=12G
#SBATCH --time=10:00:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-2

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

SUBJECT_LIST="${HOME}/clinical_dmri_benchmark/analysis/data_processing/subject_lists/preprocessed_subject_list_SS3Tautotrack.txt"
# Get the subject id from the call
subid=$(head -n "${SLURM_ARRAY_TASK_ID}" "${SUBJECT_LIST}" | tail -n 1)

SIMG="${HOME}/images/qsirecon-0.23.2.sif"
GQI_DATA_ROOT="${HOME}/results/qsirecon_outputs/qsirecon-GQIautotrack/${subid}/ses-PNC1/dwi"
SS3T_DATA_ROOT="${HOME}/results/qsirecon_outputs/qsirecon-SS3T/${subid}/ses-PNC1/dwi"
OUTPUTS="${HOME}/results/qsirecon_outputs/qsirecon-SS3Tautotrack"
PREPROCESSED_DATA_ROOT="${HOME}/results/qsiprep_outputs"
PYTHON_HELPER_SCRIPT="${HOME}/clinical_dmri_benchmark/analysis/data_processing/aggregate_atk_results.py"

# Use $TMP as the workdir
WORKDIR="${TMP}/job-${JOB_ID}_${subid}"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
mkdir -p ss3t_atk_data
mkdir -p preprocessed_data
mkdir -p ss3t_data

cp -r "${PREPROCESSED_DATA_ROOT}/${subid}" "preprocessed_data/${subid}"

# 1) Convert WM FODs from mif to fib in qsirecon and rename to match name of gqi file
for run in run-01 run-02; do
    # Copy the files we need from the source directory
    cp ${SS3T_DATA_ROOT}/${subid}_ses-PNC1*_${run}_space-T1w_model-ss3t_param-fod_label-WM_dwimap.mif.gz ss3t_data/
    source_file=$(ls ss3t_data/${subid}_ses-PNC1*_${run}_space-T1w_model-ss3t_param-fod_label-WM_dwimap.mif.gz)
    file_name=$(basename "$source_file")
    file_name_prefix="${file_name%%_space-T1w_*}_space-T1w"
    # Run command
    gunzip ${source_file}
    singularity exec --containall \
        -B "${PWD}/ss3t_data":/ss3t_data \
        -B "${PWD}/ss3t_atk_data":/ss3t_atk_data \
        -H "${PWD}" \
        "${SIMG}" \
        mif2fib --mif /ss3t_data/${file_name_prefix}_model-ss3t_param-fod_label-WM_dwimap.mif \
        --fib "/ss3t_atk_data/${file_name_prefix}_dwimap.fib"
    gzip "${PWD}/ss3t_atk_data/${file_name_prefix}_dwimap.fib"
done
# Remove files we no longer need
rm -r ss3t_data

# 2) Copy gqi .map file to the ss3t_atk directory and rename to match DSIStudio convention
for run in run-01 run-02; do
    source_file=$(ls ${GQI_DATA_ROOT}/${subid}_ses-PNC1*_${run}_space-T1w_mapping.map.gz)
    file_name=$(basename "$source_file")
    file_name_prefix="${file_name%%_space-T1w_*}_space-T1w"
    cp ${source_file} \
        "${PWD}/ss3t_atk_data/${file_name_prefix}_dwimap.fib.gz.icbm152_adult.map.gz"

    # 3) Run autotrack for both runs
    singularity exec --containall \
        -B "${PWD}/ss3t_atk_data":/ss3t_atk_data \
        "${SIMG}" \
        dsi_studio --action=atk \
        --source=/ss3t_atk_data/${file_name_prefix}_dwimap.fib.gz \
        --track_id=Association,Projection,Commissure \
        --track_voxel_ratio=2.0 \
        --yield_rate=1.0e-06 \
        --tolerance=22,26,30 \
        --trk_format=trk.gz
    # rename mapping file to match qsirecon conventions
    mv "${PWD}/ss3t_atk_data/${file_name_prefix}_dwimap.fib.gz.icbm152_adult.map.gz" \
        "${PWD}/ss3t_atk_data/${file_name_prefix}_mapping.map.gz"
done

# 4.1) Rearrange and rename bundle files and bundle stats to match qsirecon conventions
# 4.2) Convert trk.gz to tck.gz
python3 ${PYTHON_HELPER_SCRIPT} "${PWD}/ss3t_atk_data" "${subid}" "${PWD}/preprocessed_data/${subid}/ses-PNC1/dwi"

# 5) Copy to output directory
mkdir -p "${OUTPUTS}/${subid}"
mv -v "${PWD}/ss3t_atk_data"/* "${OUTPUTS}/${subid}/"
echo SUCCESS

