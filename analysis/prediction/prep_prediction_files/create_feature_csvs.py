import pandas as pd
import os
import re

subject_pattern = r"(sub-\d+)"
run_pattern = r"(run-\d+)"

excluded_subjects_file = "/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists/excluded_subjects.txt"
with open(excluded_subjects_file, 'r') as f:
    excluded_subjects = [line.strip() for line in f.readlines()]


stats_files_root = "/cbica/projects/clinical_dmri_benchmark/results/bundle_stats"
for reconstruction in ["GQIautotrack", "CSDautotrack", "SS3Tautotrack"]:
    stats_files = os.listdir(os.path.join(stats_files_root, reconstruction))
    stats_files.sort()
    if ".DS_Store" in stats_files:
        stats_files.remove(".DS_Store")
    for run in ["run-01", "run-02"]:
        # List to store individual DataFrames
        all_subjects_data = []
        for stats_file in stats_files:
            subject_id = re.search(subject_pattern, stats_file).group(1)
            if subject_id in excluded_subjects:
                continue
            run_id = re.search(run_pattern, stats_file).group(1)
            if run_id != run:
                continue
            df = pd.read_csv(os.path.join(stats_files_root, reconstruction, stats_file))
            if reconstruction == "GQIautotrack":
                df = df.drop(columns=["session_id", "task_id", "dir_id", "acq_id", "space_id", "rec_id", "run_id", "source_file"])

            # Add the subject_id column if it doesn't exist
            if 'subject_id' not in df.columns:
                df['subject_id'] = subject_id
            # Melt the DataFrame to combine `bundle` with each feature
            df_melted = df.melt(
                id_vars=['subject_id', 'bundle_name'], 
                var_name='feature', 
                value_name='value'
            )

            # Pivot the DataFrame so each unique bundle-feature becomes a column
            df_pivoted = df_melted.pivot(
                index='subject_id', 
                columns=['bundle_name', 'feature'], 
                values='value'
            )
            df_pivoted.columns = [f"{bundle}_{feature}" for bundle, feature in df_pivoted.columns]
            df_pivoted.reset_index(inplace=True)

            # Append the pivoted DataFrame to the list
            all_subjects_data.append(df_pivoted)
        df_final = pd.concat(all_subjects_data, ignore_index=True)
        df_final.to_csv(os.path.join(stats_files_root, reconstruction + "_" + run + ".csv"), index=False)
