# This script runs statistical model comparison for the main prediction analysis:
# Predicting complex reasoning from different groups of features with regressed confounds (age, sex, mean_fd)
# Two run this script, all corresponding prediction result csvs are necessary.
# They are generated using the `predict_cognition.submit` script.
from julearn.stats.corrected_ttest import corrected_ttest
import pandas as pd
from statsmodels.stats.multitest import multipletests

RESULT_ROOT = "/Users/amelie/Datasets/clinical_dmri_benchmark/prediction_results/remove_confounds_features"
TARGET = "cpxresAZv2"

def load_result_csv(path_to_csv: str, run: str, target: str, reconstruction: str, features: str = None):
    df = pd.read_csv(path_to_csv)
    df["reconstruction"] = reconstruction
    df["run"] = run.replace("-", "").replace("0", "")
    df["target"] = target[:-4]
    df["target_run"] = df["target"] + "_" + df["run"]
    if features != None:
        df["features"] = features[1:-1]
        df["run_features"] = df["run"] + "_" + df["features"]
        df["model"] = df["run"] + "_" + df["reconstruction"] + "_" + df["features"]
    else:
        df["model"] = df["target"] + "_" + df["run"] + "_" + df["reconstruction"]
    return df

# Read all result dataframes from the different prediction setups predicting the target
dfs = []
for i, run in enumerate(["run-01", "run-02"]):
    for j, reconstruction in enumerate(["GQI", "CSD", "SS3T"]):
        for k, features in enumerate(["/md-fa-volume/", "/total_volume/", "/dti_fa/", "/md/"]):
            csv_path = f"{RESULT_ROOT}/{features}/{reconstruction}_{run}_{TARGET}.csv"
            if i+j+k == 0:
                result_df = load_result_csv(csv_path, run, TARGET, reconstruction, features)
                dfs.append(result_df)
            else:
                df = load_result_csv(csv_path, run, TARGET, reconstruction, features)
                dfs.append(df)
                result_df = pd.concat([result_df, df], ignore_index=True)

# Run the corrected t-test for all considered models (2 runs * 3 reconstructions * 4 feature groups = 24)
stats_df = corrected_ttest(dfs[0], dfs[1], dfs[2], dfs[3], dfs[4], dfs[5],
                        dfs[6], dfs[7], dfs[8], dfs[9], dfs[10], dfs[11],
                        dfs[12], dfs[13], dfs[14], dfs[15], dfs[16], dfs[17],
                        dfs[18], dfs[19], dfs[20], dfs[21], dfs[22], dfs[23],
                        method="fdr_bh")

# keep only the metric we are interested in
stats_df = stats_df[stats_df["metric"] == "test_r_corr"]
stats_df = stats_df.reset_index(drop=True)

# The corrected t-test corrects for multiple comparisons by correcting for ALL comparisons
# Here, we are only interested in two groups of comparisons: 1) comparison between reconstruction methods for the same run and same group of features,
# 2) comparison between groups of features for the same reconstruction method and the same run
# -> keep only rows from the stats df comparing between models that fit category 1) or 2)
filtered_rows = []
for _, row in stats_df.iterrows():
    model_1 = row["model_1"]
    model_2 = row["model_2"]
    run_1, method_1, features_1 = model_1.split("_", 2)
    run_2, method_2, features_2 = model_2.split("_", 2)

    if ((run_1 == run_2) and (method_1 == method_2)) or ((features_1 == features_2) and (run_1 == run_2)):
        filtered_rows.append(row)
    else:
        continue
df_filtered = pd.DataFrame(filtered_rows)
df_filtered = df_filtered.reset_index(drop=True)

# Perform a correction for multiple comparisons for the selected comparisons only
rejected, pvals_corrected, _, _ = multipletests(df_filtered["p-val"], alpha=0.05, method='fdr_bh')
df_filtered["p-val-corrected"] = pvals_corrected
print(df_filtered)

# Safe the filtered dataframe with corrected p-values as csv
df_filtered.to_csv("/Users/amelie/Datasets/clinical_dmri_benchmark/prediction_results/stats_cpxres.csv", index=False)