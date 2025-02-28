# Run on juseless
from julearn import run_cross_validation, PipelineCreator
import pandas as pd
import numpy as np
from julearn.model_selection import RepeatedContinuousStratifiedKFold
from utils import filter_feature_df, filter_target_csv, get_valid_subjects, filter_confounds_csv
from julearn.utils import configure_logging
from datetime import datetime
import os
import json
import sys

configure_logging(level='INFO')
# Read global variables that vary between predictions
# Use these when running on the cluster
RUN = sys.argv[1] # [run-01, run-02]
RECONSTRUCTION = sys.argv[2] # [GQI, CSD, SS3T]
TARGET = sys.argv[3] # [cpxresAZv2, ciqAZv2, exeAZv2]
FEATURES = sys.argv[4].split(",") # [[md,dti_fa,total_volume], md, dti_fa, total_volume]
CONFOUNDS = sys.argv[5].split(",") # [[sex,ageAtScan1,mean_fd], [sex,ageAtScan1,mean_fd,mprage_antsCT_vol_TBV]]

# Use these when running / debugging one specific setup locally
# RUN = "run-02"
# RECONSTRUCTION = "SS3T"
# TARGET = "cpxresAZv2"
# FEATURES = ["total_volume"]
# CONFOUNDS = ["ageAtScan1"]

# mean_fd differs between run-01 and run-02 so we need to specify which run we are using
if "mean_fd" in CONFOUNDS:
    CONFOUNDS[CONFOUNDS.index("mean_fd")] = "mean_fd_" + RUN

# Set global variables that stay the same for all predictions
TARGET_CSV = "/data/project/clinical_dmri_benchmark/data/targets/n9498_cnb_zscores_all_fr_20161215.csv"
CONVERSION_CSV = "/data/project/clinical_dmri_benchmark/data/targets/bblid_scanid_sub.csv"
CONFOUND_CSV = "/data/project/clinical_dmri_benchmark/data/confounds/confounds.csv"
FEATURE_CSV_ROOT = "/data/project/clinical_dmri_benchmark/data/bundle_stats"
SAVE_ROOT = "/data/project/clinical_dmri_benchmark/results/remove_confounds_features"
# The default setup does not include TBV as a confound. If it is included we need to adjust the root to save results
if "mprage_antsCT_vol_TBV" in CONFOUNDS:
    SAVE_ROOT = os.path.join(SAVE_ROOT, "include_TBV")
os.makedirs(SAVE_ROOT, exist_ok=True)

MODEL = "ridge"
NORMALIZATION = "zscore"
N_QUANTILES = 5
N_REPEATS = 100
RANDOM_STATE = 22
EXCLUDED_BUNDLES = ["ProjectionBrainstem_DentatorubrothalamicTract-lr", 
                    "ProjectionBrainstem_DentatorubrothalamicTract-rl",
                    "ProjectionBrainstem_CorticobulbarTractL",
                    "ProjectionBrainstem_CorticobulbarTractR",
                    "ProjectionBasalGanglia_OpticRadiationR",
                    "ProjectionBasalGanglia_OpticRadiationL"]
ALPHA = [0.001, 0.1, 1.0, 10.0, 100.0, 500.0, 1000.0, 5000.0, 10000.0]

np.random.seed(RANDOM_STATE)

valid_subjects = get_valid_subjects(EXCLUDED_BUNDLES)

# Prep feature, target and confound csv
df_features = pd.read_csv(os.path.join(FEATURE_CSV_ROOT, RECONSTRUCTION + "autotrack_" + RUN +  ".csv"))
df_features = filter_feature_df(df_features, EXCLUDED_BUNDLES, FEATURES, valid_subjects)

df_conversion = pd.read_csv(CONVERSION_CSV)
df_targets = pd.read_csv(TARGET_CSV)
df_targets = filter_target_csv(df_targets, df_conversion, valid_subjects, TARGET)

df_confounds = filter_confounds_csv(pd.read_csv(CONFOUND_CSV), valid_subjects, CONFOUNDS)

# create global prediction df with features, target and confounds
df = pd.merge(df_features, df_targets, on="subject_id", how="inner")
df = pd.merge(df, df_confounds, on="subject_id", how="inner")

# remove rows containing NaNs. This might arrise due to missing target or confound values
df = df.dropna()

# Get all bundle-feature combos
features = []
for feature in FEATURES:
    feature_bundle_combos = df.filter(like=feature).columns.tolist()
    for feature_bundle_combo in feature_bundle_combos:
        features.append(feature_bundle_combo)

# Setup prediction pipeline (confound removal, normalization, prediction)
X_types = {"features": features, "confounds": CONFOUNDS}
creator = PipelineCreator(problem_type="regression", apply_to="features")
creator.add("confound_removal", confounds="confounds")
creator.add(NORMALIZATION, apply_to="features")
creator.add(MODEL, alpha=ALPHA)

# run prediction
scores, model, inspector = run_cross_validation(
    X=features + CONFOUNDS,
    X_types=X_types,
    y=TARGET,
    data=df,
    model=creator,
    return_train_score=True,
    scoring = ["r_corr", "r2", "neg_mean_squared_error"],
    cv=RepeatedContinuousStratifiedKFold(method="quantile", n_bins=N_QUANTILES, random_state=RANDOM_STATE, n_repeats=N_REPEATS),
    return_estimator="all",
    return_inspector=True
)

# save prediction results
if len(FEATURES) == 1:
    save_folder = FEATURES[0]
else:
    save_folder = "md-fa-volume"
folder_path = os.path.join(SAVE_ROOT, save_folder)
os.makedirs(folder_path, exist_ok=True)
save_name = RECONSTRUCTION + "_" + RUN + "_" + TARGET

cv_predictions = inspector.folds.predict()
metadata = {
    "run": RUN,
    "reconstruction": RECONSTRUCTION,
    "excluded bundles": EXCLUDED_BUNDLES,
    "model": MODEL,
    "target": TARGET,
    "alphas": ALPHA,
    "normalization": NORMALIZATION,
    "features": FEATURES,
    "number_of_features": len(features),
    "n_quantiles": N_QUANTILES,
    "n_repeats": N_REPEATS,
    "random_state": RANDOM_STATE,
    "confounds": CONFOUNDS,
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}
scores.to_csv(os.path.join(SAVE_ROOT, save_folder, save_name + ".csv"))
with open(os.path.join(SAVE_ROOT, save_folder, save_name + ".json"), "w") as f:
    json.dump(metadata, f, indent=4)
cv_predictions.to_csv(os.path.join(SAVE_ROOT, save_folder, save_name + "_inspector.csv"))