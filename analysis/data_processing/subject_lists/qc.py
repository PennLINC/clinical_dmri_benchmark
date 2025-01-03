import pandas as pd
from pathlib import Path

QC_FILE = "/cbica/projects/clinical_dmri_benchmark/data/QC/n1601_dti_qa_20170301.csv"
MAPPING_FILE = "/cbica/projects/clinical_dmri_benchmark/data/QC/bblid_scanid_sub.csv"
EXCLUDED_SBJS = Path("/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists/excluded_subjects.txt")

# Check if a list of excluded subjects already exists
# If it doesn't, create a file and an empty list
if not EXCLUDED_SBJS.exists():
    EXCLUDED_SBJS.touch()
    already_excluded_sbjs = []
# If it does, read the IDs it already contains
else:
    with open(EXCLUDED_SBJS, 'r') as file:
        already_excluded_sbjs = [line.strip() for line in file if line.strip()]
    # This step is necessary to ensure there are no more empty lines at the end of the file
    with open(EXCLUDED_SBJS, 'w') as file:
        for id in already_excluded_sbjs:
            file.write(f"{id}\n")

df_qc = pd.read_csv(QC_FILE)
# There is also a dti32Exclude column but this is identical to the dti64Exclude column
df_qc = df_qc[["bblid", "dti64Exclude"]]
excluded_subjects = df_qc[df_qc["dti64Exclude"] == 1]["bblid"].values

# Convert the IDs from the QC file to the IDs used in our analysis
# If the ID is not already in the list of excluded subjects, add it to the txt file
mapfile = pd.read_csv(MAPPING_FILE)
for subject in excluded_subjects:
    sub_id = mapfile[mapfile["bblid"] == subject]["rbcid"].values[0]
    sub_id = "sub-" + str(sub_id)
    if sub_id not in already_excluded_sbjs:
        with open(EXCLUDED_SBJS, 'a') as file:
            file.write(f"{sub_id}\n")
    else:
        continue
