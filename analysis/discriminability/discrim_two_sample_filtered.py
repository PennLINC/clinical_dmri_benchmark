import pandas as pd
import os
import numpy as np
import re
from hyppo.discrim import DiscrimTwoSample
import argparse

# Helper function to load reconstruction data
def load_reconstruction_data(dice_root, recon_suffix, bundle):
    dice_path = os.path.join(dice_root, recon_suffix, bundle + ".csv")
    dices = pd.read_csv(dice_path, index_col=0, na_values=[""]).values
    distances = 1 - dices
    subject_ids = pd.read_csv(dice_path, nrows=0).columns.values[1:]
    subject_ids = np.array([re.sub(r"sub-", "", col) for col in subject_ids])
    rows_to_keep = ~np.isnan(distances).all(axis=1)
    distances = distances[rows_to_keep]
    distances = distances[:, rows_to_keep]
    subject_ids = subject_ids[rows_to_keep]
    return distances, subject_ids

# Helper function to filter for common subject IDs
def filter_common(subject_ids, distances, common_subids):
    indices = [i for i, sub in enumerate(subject_ids) if sub in common_subids]
    filtered_subject_ids = subject_ids[indices]
    filtered_distances = distances[np.ix_(indices, indices)]
    return filtered_subject_ids, filtered_distances

# Helper function to filter isolates from the common subject IDs
def filter_isolates(common_subids):
    # Simplify subject IDs to exclude run-specific information
    simplified_subids = np.array([re.sub(r"\_run-\d+", "", sub) for sub in common_subids])

    # Identify entries that appear more than once
    unique, counts = np.unique(simplified_subids, return_counts=True)
    repeated_entries = unique[counts > 1]

    # Create a mask for common_subids
    mask = np.isin(simplified_subids, repeated_entries)
    return mask

# Helper function to apply an isolate mask
def apply_isolate_mask(subject_ids, distances, mask):
    subject_ids = subject_ids[mask]
    distances = distances[np.ix_(mask, mask)]
    return subject_ids, distances

# Main function
def get_discrim_two_sample(dice_root: str, recon_suffix_1: str, recon_suffix_2: str, recon_suffix_3: str, bundle_names: list, output_path: str, workers: int):
    """
    Parameters:
    ----------
    dice_root : str
        Root directory containing reconstruction data.
    recon_suffix_1 : str
        Suffix for the first reconstruction.
    recon_suffix_2 : str
        Suffix for the second reconstruction.
    recon_suffix_3 : str
        Suffix for the third reconstruction (used for filtering only).
    bundle_names : list
        List of bundle names.
    output_path : str
        Path to save the output CSV file.
    """
    df = pd.DataFrame(columns=["bundle", "discrim_" + recon_suffix_1, "discrim_" + recon_suffix_2, "p-value"])
    for bundle in bundle_names:
        print(bundle)

        # Load data for all three reconstructions
        distances_1, subject_ids_1 = load_reconstruction_data(dice_root, recon_suffix_1, bundle)
        distances_2, subject_ids_2 = load_reconstruction_data(dice_root, recon_suffix_2, bundle)
        distances_3, subject_ids_3 = load_reconstruction_data(dice_root, recon_suffix_3, bundle)

        # Find common subject IDs across all three reconstructions
        common_subids = np.intersect1d(
            np.intersect1d(subject_ids_1, subject_ids_2), subject_ids_3
        )

        # Filter distance matrices and subject IDs for common combinations
        subject_ids_1, distances_1 = filter_common(subject_ids_1, distances_1, common_subids)
        subject_ids_2, distances_2 = filter_common(subject_ids_2, distances_2, common_subids)
        subject_ids_3, distances_3 = filter_common(subject_ids_3, distances_3, common_subids)

        # Remove isolates
        isolate_mask = filter_isolates(common_subids)
        subject_ids_1, distances_1 = apply_isolate_mask(subject_ids_1, distances_1, isolate_mask)
        subject_ids_2, distances_2 = apply_isolate_mask(subject_ids_2, distances_2, isolate_mask)
        subject_ids_1 = np.array([re.sub(r"\_run-\d+", "", sub) for sub in subject_ids_1])

        # Compute discriminability for the first two reconstructions
        two_sample_output = DiscrimTwoSample(is_dist=True).test(distances_1, distances_2, subject_ids_1, workers=workers)
        df_row = {
            "bundle": bundle,
            "discrim_" + recon_suffix_1: two_sample_output.d1,
            "discrim_" + recon_suffix_2: two_sample_output.d2,
            "p-value": two_sample_output.pvalue,
        }
        print(df_row)
        df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)

    df.to_csv(output_path, index=False)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruction method")
    parser.add_argument(
        "--recon_suffix_1",
        type=str,
        required=True,
        help="Reconstruction method (e.g., GQIautotrack)",
    )
    parser.add_argument(
        "--recon_suffix_2",
        type=str,
        required=True,
        help="Reconstruction method (e.g., GQIautotrack)",
    )
    parser.add_argument(
        "--recon_suffix_3",
        type=str,
        required=True,
        help="Reconstruction method (e.g., GQIautotrack)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        required=True,
        help="Num CPUs available for permutation testing",
    )
    args = parser.parse_args()
    QSIRECON_SUFFIX_1 = args.recon_suffix_1
    QSIRECON_SUFFIX_2 = args.recon_suffix_2
    QSIRECON_SUFFIX_3 = args.recon_suffix_3
    WORKERS = args.workers
    DICE_ROOT = "/cbica/projects/clinical_dmri_benchmark/results/dices/"
    BUNDLE_NAMES = "/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/data/bundle_names.txt"
    OUTPUT_PATH = (
        "/cbica/projects/clinical_dmri_benchmark/results/discriminability/two_sample_"
        + QSIRECON_SUFFIX_1 + "_" + QSIRECON_SUFFIX_2
        + ".csv"
    )

    with open(BUNDLE_NAMES, "r") as f:
        bundles = f.read().splitlines()
    for i, bundle in enumerate(bundles):
        bundles[i] = bundle.replace("_", "").replace("-", "")

    get_discrim_two_sample(DICE_ROOT, QSIRECON_SUFFIX_1, QSIRECON_SUFFIX_2, QSIRECON_SUFFIX_3, bundles, OUTPUT_PATH, WORKERS)
