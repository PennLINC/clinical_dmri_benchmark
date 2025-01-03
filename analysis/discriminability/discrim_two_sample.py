import pandas as pd
import os
import numpy as np
import re
from hyppo.discrim import DiscrimTwoSample
import argparse

def get_discrim_two_sample(dice_root: str, recon_suffix_1: str, recon_suffix_2: str, bundle_names: list, output_path: str):
    """

    Parameters:
    ----------
    
    """
    df = pd.DataFrame(columns=["bundle", "discrim_" + recon_suffix_1, "discrim_" + recon_suffix_2, "null_distr"])
    for bundle in bundle_names:
        print(bundle)
        dice_path_1 = os.path.join(dice_root, recon_suffix_1, bundle + ".csv")
        dices_1 = pd.read_csv(dice_path_1, index_col=0, na_values=[""]).values
        distances_1 = 1 - dices_1
        subject_ids_1 = pd.read_csv(dice_path_1, nrows=0).columns.values[1:]
        subject_ids_1 = np.array(
            [re.sub(r"sub-", "", col) for col in subject_ids_1]
        )

        dice_path_2 = os.path.join(dice_root, recon_suffix_2, bundle + ".csv")
        dices_2 = pd.read_csv(dice_path_2, index_col=0, na_values=[""]).values
        distances_2 = 1 - dices_2
        subject_ids_2 = pd.read_csv(dice_path_2, nrows=0).columns.values[1:]
        subject_ids_2 = np.array(
            [re.sub(r"sub-", "", col) for col in subject_ids_2]
        )

        # Remove rows and columns from the distance matrix that only contain NaNs
        # This will exclude runs that the bundle of interest couldn't be reconstructed for
        rows_to_keep_1 = ~np.isnan(distances_1).all(axis=1)
        distances_1 = distances_1[rows_to_keep_1]
        distances_1 = distances_1[:, rows_to_keep_1]
        subject_ids_1 = subject_ids_1[rows_to_keep_1]
        rows_to_keep_2 = ~np.isnan(distances_2).all(axis=1)
        distances_2 = distances_2[rows_to_keep_2]
        distances_2 = distances_2[:, rows_to_keep_2]
        subject_ids_2 = subject_ids_2[rows_to_keep_2]

        # Remove all subID-run combos that are not present in both vectors / distance matrices
        # Step 1: Find the common subject-run combinations
        common_subids = np.intersect1d(subject_ids_1, subject_ids_2)
        # Step 2: Find indices of common combinations in both vectors
        indices1 = [i for i, sub in enumerate(subject_ids_1) if sub in common_subids]
        indices2 = [i for i, sub in enumerate(subject_ids_2) if sub in common_subids]
        filtered_subids_1 = subject_ids_1[indices1]
        filtered_subids_2 = subject_ids_2[indices2]
        print((filtered_subids_1 == filtered_subids_2).all())
        # Step 3: Filter matrices accordingly
        filtered_distances_1 = distances_1[np.ix_(indices1, indices1)]
        filtered_distances_2 = distances_2[np.ix_(indices2, indices2)]        
        common_subids = np.array(
            [re.sub(r"\_run-\d+", "", col) for col in common_subids]
       	)
        
        # remove isolates
        # Step 1: Identify entries that appear more than once
        (unique, counts) = np.unique(common_subids, return_counts=True)
        repeated_entries = unique[counts > 1]  # Only keep entries appearing more than once

        # Step 2: Create a mask for entries to keep
        mask = np.isin(common_subids, repeated_entries)

        # Step 3: Filter the array and matrices
        common_subids = common_subids[mask]
        filtered_distances_1 = filtered_distances_1[np.ix_(mask, mask)]
        filtered_distances_2 = filtered_distances_2[np.ix_(mask, mask)]

        two_sample_output = DiscrimTwoSample(is_dist=True).test(filtered_distances_1, filtered_distances_2, common_subids)
        df_row = {
            "bundle": bundle,
            "discrim_" + recon_suffix_1: two_sample_output.d1,
            "discrim_" + recon_suffix_2: two_sample_output.d2,
            "p-value": two_sample_output.pvalue
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
    args = parser.parse_args()
    QSIRECON_SUFFIX_1 = args.recon_suffix_1
    QSIRECON_SUFFIX_2 = args.recon_suffix_2
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

    get_discrim_two_sample(DICE_ROOT, QSIRECON_SUFFIX_1, QSIRECON_SUFFIX_2, bundles, OUTPUT_PATH)
