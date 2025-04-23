import os
import pandas as pd
import glob
import numpy as np

OUTPUT_ROOT = "/cbica/projects/clinical_dmri_benchmark/results/qsiprep_outputs"
CONFOUNDS_ROOT = "/cbica/projects/clinical_dmri_benchmark/data/prediction/confounds"
ID_CONVERSION_PATH = "/cbica/projects/clinical_dmri_benchmark/data/QC/bblid_scanid_sub.csv"
subject_ids = [f for f in os.listdir(
    OUTPUT_ROOT) if os.path.isdir(os.path.join(OUTPUT_ROOT, f))]
if "failures" in subject_ids:
    subject_ids.remove("failures")


def find_qc_csv(folder, subid, run):
    pattern = os.path.join(
        folder, f"{subid}_ses-PNC1_*{run}_desc-ImageQC_dwi.csv")
    matching_files = glob.glob(pattern)

    if matching_files:
        # Return the first match (assuming only one correct file per folder)
        return matching_files[0]
    else:
        return None  # No matching file found


# 1) Create csv file with max and mean fd per scan
head_motion_list = []
for subject_id in subject_ids:
    sub_head_motion_list = [subject_id, np.nan, np.nan, np.nan, np.nan]
    for i, run in enumerate(["run-01", "run-02"]):
        extended_root = os.path.join(
            OUTPUT_ROOT, subject_id, "ses-PNC1", "dwi")
        qc_file = find_qc_csv(extended_root, subject_id, run)
        if qc_file is not None:
            qc_df = pd.read_csv(qc_file)
            if len(qc_df["mean_fd"].values > 0):
                sub_head_motion_list[i*2+1] = qc_df["mean_fd"].values[0]
            if len(qc_df["max_fd"].values > 0):
                sub_head_motion_list[i*2+2] = qc_df["max_fd"].values[0]
        else:
            sub_head_motion_list[i] = np.nan
            sub_head_motion_list[i+1] = np.nan
    head_motion_list.append(sub_head_motion_list)
head_motion_df = pd.DataFrame(head_motion_list, columns=[
                              "subject_id", "mean_fd_run-01", "max_fd_run-01", "mean_fd_run-02", "mean_fd_run-02"])
head_motion_df.to_csv(os.path.join(
    CONFOUNDS_ROOT, "head_motion.csv"), index=False)

# 2) Merge information from head motion csv, demographics csv and TBV csv to one confounds csv
head_motion = pd.read_csv(os.path.join(CONFOUNDS_ROOT, "head_motion.csv"))
demographics = pd.read_csv(os.path.join(
    CONFOUNDS_ROOT, "n1601_demographics_go1_20161212.csv"))
tbv = pd.read_csv(os.path.join(CONFOUNDS_ROOT, "n1601_ctVol20170412.csv"))[
    ["bblid", "mprage_antsCT_vol_TBV"]]
id_conversion_file = pd.read_csv(ID_CONVERSION_PATH)
id_conversion_file = id_conversion_file.rename(columns={"bbl_id": "bblid"})

merged_df = pd.merge(demographics, tbv, on="bblid", how="inner")
merged_df = pd.merge(merged_df, id_conversion_file, on="bblid", how="inner")
merged_df = merged_df.drop(columns=["scanid_x", "scanid_y", "bblid"])
merged_df["rbcid"] = "sub-" + merged_df["rbcid"].astype(str)
merged_df = merged_df.rename(columns={"rbcid": "subject_id"})
merged_df = pd.merge(head_motion, merged_df, on="subject_id", how="inner")
merged_df.to_csv(os.path.join(CONFOUNDS_ROOT, "confounds.csv"))
