import pandas as pd
import os


def get_valid_subjects(fractions_root: str, excluded_bundles: list = []) -> list:
    """
    This function returns subject ids of subjects that have all bundles considered for prediction
    reconstructed for both runs for all three reconstruction methods. Excluding bundles with low 
    reconstruction fractions increases the number of valid subjects.

    Args:
      fractions_root: Path to the folder where reconstruction fractions are saved
      excluded_bundles: List of bundles that should not be included in the prediction analysis.
      Optional, defaults to empty list.

    Returns:
      List of valid subject ids
    """
    valid_subjects = []
    excluded_bundles_short = []
    for i in range(len(excluded_bundles)):
        excluded_bundles_short.append(
            excluded_bundles[i].replace("_", "").replace("-", ""))
    for reconstruction in ["GQIautotrack", "CSDautotrack", "SS3Tautotrack"]:
        fractions_file_name = os.path.join(
            fractions_root, "reconstructed_bundles_" + reconstruction + ".csv")
        fractions_df = pd.read_csv(fractions_file_name, index_col=0).drop(
            columns=excluded_bundles_short)
        bundle_columns = fractions_df.columns.difference(
            ["subject_id", "run"])  # Identify bundle columns
        # Step 1: Group by subject_id and run
        grouped = fractions_df.groupby(["subject_id", "run"])[
            bundle_columns].all()
        # Step 2: Check if all rows per subject_id-run are True
        all_runs = grouped.groupby("subject_id").all()
        # Step 3: Filter subject_ids where all rows for all runs are True
        valid_subjects.append(all_runs[all_runs.all(axis=1)].index.tolist())
    valid_subjects = list(set(valid_subjects[0]) & set(
        valid_subjects[1]) & set(valid_subjects[2]))
    return valid_subjects


def filter_feature_df(df: pd.DataFrame, excluded_bundles: list, features: list, valid_subjects: list) -> pd.DataFrame:
    """Filter the dataframe containing all features for all subjects to only contain valid subjects
    (with all considered bundles reconstructed for both runs) and only the selected features for bundles
    considered for prediction.

    Args:
      df: A dataframe containing features as columns and subjects as rows
      excluded_bundles: A list of bundles not considered for the prediction analysis due to low
      reconstruction fractions
      features: A list of features considered for prediction (e.g. md, dti_fa)
      valid_subjects: A list of all subjects that have all bundles considered for prediction
      reconstructed for both runs (i.e. all subjects without missing features)

    Returns:
      Filtered dataframe
    """
    features = features.copy()
    # drop invalid subjects
    df = df[df["subject_id"].isin(valid_subjects)]

    # drop features from excluded bundles
    for excluded_bundle in excluded_bundles:
        df = df.loc[:, ~df.columns.str.contains(excluded_bundle)]

    # keep selected features only
    features.append("subject_id")
    df = df.filter(regex="|".join(features), axis=1)
    return df


def filter_target_csv(target_csv: pd.DataFrame, conversion_csv: pd.DataFrame, valid_subjects: list, target: str) -> pd.DataFrame:
    """Filter the dataframe containing all targets for all subjects to only contain valid subjects
    (with all considered bundles reconstructed for both runs) and only the selected target.

    Args:
      target_csv: A dataframe containing all targets and bblids
      conversion_csv: A dataframe containing bblids and rbcids to convert between both id systems
      valid_subjects: A list of all subjects that have all bundles considered for prediction
      reconstructed for both runs (i.e. all subjects without missing features)
      target: The target considered for prediction

    Returns:
      Filtered dataframe
    """
    # convert bblid to rbcid with help of conversion csv file
    conversion_csv = conversion_csv.rename(columns={"bbl_id": "bblid"})
    merged_df = pd.merge(conversion_csv, target_csv, on="bblid", how="inner")
    merged_df["rbcid"] = "sub-" + merged_df["rbcid"].astype(str)

    # drop invalid subjects
    merged_df = merged_df[merged_df["rbcid"].isin(valid_subjects)]

    # keep only subject ID and target of interest
    merged_df = merged_df.rename(columns={"rbcid": "subject_id"})
    final_df = merged_df[["subject_id", target]]
    return final_df


def filter_confounds_csv(confounds_csv: pd.DataFrame, valid_subjects: list, confounds: list) -> pd.DataFrame:
    """Filter the dataframe containing all confounds for all subjects to only contain valid subjects
    (with all considered bundles reconstructed for both runs) and only the selected confounds.

    Args:
      confounds_csv: A dataframe containing all confounds and subject_ids
      valid_subjects: A list of all subjects that have all bundles considered for prediction
      reconstructed for both runs (i.e. all subjects without missing features)
      confounds: A list of confounds to be considered in the analysis

    Returns:
      Filtered dataframe
    """
    # drop invalid subjects
    confounds_csv = confounds_csv[confounds_csv["subject_id"].isin(
        valid_subjects)]
    confounds = confounds.copy()
    confounds.append("subject_id")
    confounds_csv = confounds_csv[confounds]
    return confounds_csv
