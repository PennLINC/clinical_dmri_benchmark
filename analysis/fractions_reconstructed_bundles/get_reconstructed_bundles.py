import os
import pandas as pd
import glob
import argparse


def get_reconstructed_bundles(
    data_root: str, bundles: list, output_path: str, excluded_subjects: list = None
):
    """
    Generates a DataFrame of reconstructed bundles for each subject and saves it to a CSV file.

    This function iterates through subject directories within the specified `data_root` directory, checking for the presence of bundle reconstruction files for each specified bundle in each subject's directory.
    The function builds a DataFrame with each row representing a subject and run, and each column indicating the presence (1) or absence (0) of a specific bundle's reconstruction.
    It then saves this DataFrame to the specified `output_path` as a CSV file.

    Args:
        data_root (str): Path to the root directory containing subject data folders.
                         Each subject folder should start with 'sub' and contain reconstructed bundles.
        bundles (list): List of bundle names to check for each subject.
                        Each bundle is expected to have a corresponding file in the subject's folder.
        output_path (str): File path for the output CSV file.
                           The CSV will contain a binary indicator (1 or 0) for the presence of each bundle in each run for each subject.
        excluded_subjects (list, optional): List of subject IDs to exclude from the analysis.
                                            If provided, these subjects will not be included in the output CSV file.

    Returns:
        None: This function does not return any value. It saves the result as a CSV file at the specified `output_path`.
    """
    # get all subjects that were reconstructed with the specified reconstruction
    subjects = [
        name
        for name in os.listdir(data_root)
        if os.path.isdir(os.path.join(data_root, name)) and name.startswith("sub")
    ]
    # remove excluded subjects if provided
    if excluded_subjects is not None:
        for subject in excluded_subjects:
            if subject in subjects:
                subjects.remove(subject)

    columns = bundles.copy()
    columns.insert(0, "subject_id")
    columns.insert(1, "run")

    df = pd.DataFrame(columns=columns)

    for subject in subjects:
        print(subject)
        for run in ["run-01", "run-02"]:
            df_row = [subject, run]
            for bundle in bundles:
                bundle_path = os.path.join(
                    ROOT_QSIRECON,
                    subject,
                    "ses-PNC1",
                    "dwi",
                    f"{subject}_ses-PNC1_*{run}_space-T1w_bundle-{bundle}_streamlines.tck.gz",
                )
                matching_files = glob.glob(bundle_path)
                if matching_files:
                    df_row.append(1)
                else:
                    df_row.append(0)
            df.loc[(len(df))] = df_row
    df.to_csv(output_path)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruction method")
    parser.add_argument(
        "--recon_suffix",
        type=str,
        required=True,
        help="Reconstruction method (e.g., GQIautotrack)",
    )
    args = parser.parse_args()
    QSIRECON_SUFFIX = args.recon_suffix
    ROOT_QSIRECON = os.path.join(
        "/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs",
        "qsirecon-" + QSIRECON_SUFFIX,
    )
    OUTPUT_PATH = (
        "/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/reconstructed_bundles_"
        + QSIRECON_SUFFIX
        + ".csv"
    )
    BUNDLE_NAMES = "../../data/bundle_names.txt"
    EXCLUDED_SBJ_LIST = "../data_processing/subject_lists/excluded_subjects.txt"

    with open(BUNDLE_NAMES, "r") as f:
        bundles = f.read().splitlines()
    for i, bundle in enumerate(bundles):
        bundles[i] = bundle.replace("_", "").replace("-", "")
    with open(EXCLUDED_SBJ_LIST, "r") as f:
        excluded_subjects = f.read().splitlines()

    get_reconstructed_bundles(
        ROOT_QSIRECON, bundles, OUTPUT_PATH, excluded_subjects
    )
