import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

QC_FILE = "/cbica/projects/clinical_dmri_benchmark/data/QC/n1601_dti_qa_20170301.csv"
MAPPING_FILE = "/cbica/projects/clinical_dmri_benchmark/data/QC/bblid_scanid_sub.csv"
EXCLUDED_SBJS = Path(
    "/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists/excluded_subjects.txt")
RECONSTRUCTION_OUTPUTS = Path(
    "/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/qsirecon-GQIautotrack")

# Check if a list of excluded subjects already exists
# If it doesn't, create a file and an empty list
if not EXCLUDED_SBJS.exists():
    EXCLUDED_SBJS.touch()
    excluded_sbjs = []
# If it does, read the IDs it already contains
else:
    with open(EXCLUDED_SBJS, 'r') as file:
        excluded_sbjs = [line.strip() for line in file if line.strip()]


# 1) Add subject IDs of subjects that crashed during reconstruction
failed_reconstructions = RECONSTRUCTION_OUTPUTS / "failures"
failed_subject_ids = [
    f.name for f in failed_reconstructions.iterdir() if f.is_dir()]
logging.info(
    f"Found {len(failed_subject_ids)} subjects that reconstruction failed for.")
for failed_subject_id in failed_subject_ids:
    if failed_subject_id not in excluded_sbjs:
        excluded_sbjs.append(failed_subject_id)

# 2) Add subject IDs of subjects with acquisition variants other than missing fieldmaps
reconstructed_subject_ids = [
    f.name for f in RECONSTRUCTION_OUTPUTS.iterdir() if f.is_dir()]
reconstructed_subject_ids.remove("failures")
acq_variant_counter = 0
for reconstructed_subject in reconstructed_subject_ids:
    subject_path = RECONSTRUCTION_OUTPUTS / \
        reconstructed_subject / "ses-PNC1" / "dwi"
    dwimap_file = [f for f in subject_path.iterdir() if f.is_file(
    ) and "run-01_space-T1w_dwimap.fib" in f.name][0].name
    # We want to exclude all acquisition variants except missing fieldmaps
    # since we are not using fieldmaps in our analysis and it doesn't make a difference if they are missing
    if ("acq-VARIANT" in dwimap_file) and ("NoFmap" not in dwimap_file):
        if reconstructed_subject not in excluded_sbjs:
            excluded_sbjs.append(reconstructed_subject)
            acq_variant_counter += 1
logging.info(
    f"Found {acq_variant_counter} subjects that were acquired with an acquisition variant.")

# 3) Add subject IDs of subjects that failed QC based on Roalf et al., 2016
df_qc = pd.read_csv(QC_FILE)
# There is also a dti32Exclude column but this is identical to the dti64Exclude column
df_qc = df_qc[["bblid", "dti64Exclude"]]
# Since the bblid differs from the ID system used here, we use a mapping file to convert
# the bblids to the project's id system
mapfile = pd.read_csv(MAPPING_FILE)
mapfile["subject_id"] = "sub-" + mapfile["rbcid"].astype(str)
df_qc = pd.merge(df_qc, mapfile, on='bblid', how='inner')

failed_qc_counter = 0
excluded_subjects_qc = list(
    df_qc[df_qc["dti64Exclude"] == 1]["subject_id"].values)
for excluded_subject in excluded_subjects_qc:
    if (excluded_subject in reconstructed_subject_ids) and (excluded_subject not in excluded_sbjs):
        failed_qc_counter += 1
        excluded_sbjs.append(excluded_subject)
logging.info(f"Found {failed_qc_counter} subjects that failed QC.")

# 4) Write all the ids of excluded subjects to the excluded subjects file
with open(EXCLUDED_SBJS, 'w') as file:
    for excluded_subject in excluded_sbjs:
        file.write(f"{excluded_subject}\n")
