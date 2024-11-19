#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=6G
#SBATCH --time=08:00:00
#SBATCH --output=../logs/pnc-%A_%a.log
#SBATCH --array=1-1397

[ -z "${JOB_ID}" ] && JOB_ID=TEST

if [[ ! -z "${SLURM_JOB_ID}" ]]; then
    echo SLURM detected
    JOB_ID="${SLURM_JOB_ID}"
    NSLOTS="${SLURM_JOB_CPUS_PER_NODE}"
fi

SUBJECT_LIST="${HOME}/clinical_dmri_benchmark/analysis/data_processing/subject_lists/preprocessed_subject_list_CSDautotrack.txt"
# Get the subject id from the call
subid=$(head -n "${SLURM_ARRAY_TASK_ID}" "${SUBJECT_LIST}" | tail -n 1)

SIMG="${HOME}/images/qsirecon-0.23.2.sif"
GQI_DATA_ROOT="${HOME}/results/qsirecon_outputs/qsirecon-GQIautotrack/${subid}/ses-PNC1/dwi"
CSD_DATA_ROOT="${HOME}/results/qsirecon_outputs/qsirecon-CSD/${subid}/ses-PNC1/dwi"
OUTPUTS="${HOME}/results/qsirecon_outputs/qsirecon-CSDautotrack"
PREPROCESSED_DATA_ROOT="${HOME}/results/qsiprep_outputs"
PYTHON_HELPER_SCRIPT_1="${HOME}/clinical_dmri_benchmark/analysis/data_processing/combine_gqi_csd_fibs.py"
PYTHON_HELPER_SCRIPT_2="${HOME}/clinical_dmri_benchmark/analysis/data_processing/aggregate_atk_results.py"

# Use $TMP as the workdir
WORKDIR="${TMP}/job-${JOB_ID}_${subid}"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
mkdir -p csd_atk_data
mkdir -p preprocessed_data
mkdir -p csd_data

cp -r "${PREPROCESSED_DATA_ROOT}/${subid}" "preprocessed_data/${subid}"

# 1) Convert WM FODs from mif to fib in qsirecon and rename to match name of gqi file
for run in run-01 run-02; do
    # Copy the files we need from the source directory
    cp ${CSD_DATA_ROOT}/${subid}_ses-PNC1*_${run}_space-T1w_model-csd_param-fod_label-WM_dwimap.mif.gz csd_data/
    source_file=$(ls csd_data/${subid}_ses-PNC1*_${run}_space-T1w_model-csd_param-fod_label-WM_dwimap.mif.gz)
    file_name=$(basename "$source_file")
    file_name_prefix="${file_name%%_space-T1w_*}_space-T1w"
    # Run command
    gunzip ${source_file}
    singularity exec --containall \
        -B "${PWD}/csd_data":/csd_data \
        -B "${PWD}/csd_atk_data":/csd_atk_data \
        -H "${PWD}" \
        "${SIMG}" \
        mif2fib --mif /csd_data/${file_name_prefix}_model-csd_param-fod_label-WM_dwimap.mif \
        --fib "/csd_atk_data/${file_name_prefix}_dwimap.fib"
    
done
# Remove files we no longer need
rm -r csd_data

# 2) Add the DTI maps from the GQI fib file to the csd fib file
for run in run-01 run-02; do
    gqi_fib_file=$(ls ${GQI_DATA_ROOT}/${subid}_ses-PNC1*_${run}_space-T1w_dwimap.fib.gz)
    gqi_file_name=$(basename "$gqi_fib_file")
    gqi_file_name_prefix=${gqi_file_name%%_space-T1w_*}_space-T1w
    csd_file=$(ls csd_atk_data/${subid}_ses-PNC1*_${run}_space-T1w_dwimap.fib)
    csd_file_name=$(basename "$csd_file")
    csd_file_name_prefix=${csd_file_name%%_space-T1w_*}_space-T1w
    gunzip ${gqi_fib_file}
    python3 ${PYTHON_HELPER_SCRIPT_1} --gqi_path "${GQI_DATA_ROOT}/${gqi_file_name_prefix}_dwimap.fib" --csd_path "csd_atk_data/${csd_file_name_prefix}_dwimap.fib"
    gzip "${GQI_DATA_ROOT}/${gqi_file_name_prefix}_dwimap.fib"
    gzip "csd_atk_data/${csd_file_name_prefix}_dwimap.fib"
done

# 3) Copy gqi .map file to the csd_atk directory and rename to match DSIStudio convention
for run in run-01 run-02; do
    source_file=$(ls ${GQI_DATA_ROOT}/${subid}_ses-PNC1*_${run}_space-T1w_mapping.map.gz)
    file_name=$(basename "$source_file")
    file_name_prefix="${file_name%%_space-T1w_*}_space-T1w"
    cp ${source_file} \
        "${PWD}/csd_atk_data/${file_name_prefix}_dwimap.fib.gz.icbm152_adult.map.gz"

    # 4) Run autotrack for both runs
    singularity exec --containall \
        -B "${PWD}/csd_atk_data":/csd_atk_data \
        "${SIMG}" \
        dsi_studio --action=atk \
        --source=/csd_atk_data/${file_name_prefix}_dwimap.fib.gz \
        --track_id=Association,Projection,Commissure \
        --track_voxel_ratio=2.0 \
        --yield_rate=1.0e-06 \
        --tolerance=22,26,30 \
        --trk_format=trk.gz \
        --thread_count="${SLURM_JOB_CPUS_PER_NODE}"
    # rename mapping file to match qsirecon conventions
    mv "${PWD}/csd_atk_data/${file_name_prefix}_dwimap.fib.gz.icbm152_adult.map.gz" \
        "${PWD}/csd_atk_data/${file_name_prefix}_mapping.map.gz"
done

# 5.1) Rearrange and rename bundle files and bundle stats to match qsirecon conventions
# 5.2) Convert trk.gz to tck.gz
python3 ${PYTHON_HELPER_SCRIPT_2} "${PWD}/csd_atk_data" "${subid}" "${PWD}/preprocessed_data/${subid}/ses-PNC1/dwi"

# 6) Copy to output directory
mkdir -p "${OUTPUTS}/${subid}/ses-PNC1/dwi"
mv -v "${PWD}/csd_atk_data"/* "${OUTPUTS}/${subid}/ses-PNC1/dwi"
echo SUCCESS
