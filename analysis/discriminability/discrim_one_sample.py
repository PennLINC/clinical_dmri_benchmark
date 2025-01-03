import pandas as pd
import os
import numpy as np
import re
from hyppo.discrim import DiscrimOneSample
import argparse


def get_discrim_one_sample(dice_root: str, bundle_names: list, output_path: str):
    """
    Calculate discriminability scores for a set of bundles and save the results to a CSV file.

    This function computes a discriminability test for each bundle in `bundle_names`, based on 
    distance matrices derived from dice scores (1 - dice similarity). For each bundle, it loads 
    the dice score matrix, transforms it to a distance matrix, removes rows and columns with 
    only NaN values (indicating missing data), and performs a one-sample discriminability test 
    using the hyppo `DiscrimOneSample` function. The results for each bundle are stored in a 
    DataFrame and then saved to a specified CSV file.

    Parameters:
    ----------
    dice_root : str
        The root directory containing dice score CSV files for each bundle. Each file should 
        be named as "{bundle}.csv" and contain a matrix of dice scores with subjects as columns 
        and rows.
    bundle_names : list of str
        List of bundle names to process. Each bundle name corresponds to a CSV file in `dice_root`.
    output_path : str
        Path to save the resulting CSV file containing the discriminability scores, p-values, 
        and null distribution for each bundle.
    """
    df = pd.DataFrame(columns=["bundle", "discriminability", "p-value", "null_distr"])
    for bundle in bundle_names:
        print(bundle)
        dice_path = os.path.join(dice_root, bundle + ".csv")
        dices = pd.read_csv(dice_path, index_col=0, na_values=[""]).values
        distances = 1 - dices
        subject_ids = pd.read_csv(dice_path, nrows=0).columns.values[1:]
        subject_ids = np.array(
            [re.sub(r"sub-|\_run-\d+", "", col) for col in subject_ids]
        )

        # Remove rows and columns from the distance matrix that only contain NaNs
        # This will exclude runs that the bundle of interest couldn't be reconstructed for
        rows_to_keep = ~np.isnan(distances).all(axis=1)
        distances = distances[rows_to_keep]
        distances = distances[:, rows_to_keep]
        # Remove these rows from the ID-list as well
        subject_ids = subject_ids[rows_to_keep]
        one_sample_output = DiscrimOneSample(is_dist=True).test(distances, subject_ids)
        df_row = {
            "bundle": bundle,
            "discriminability": one_sample_output.stat,
            "p-value": one_sample_output.pvalue,
            "null_distr": one_sample_output.null_dist,
        }
        print(df_row)
        df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
    df.to_csv(output_path, index=False)
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
    DICE_ROOT = (
        "/cbica/projects/clinical_dmri_benchmark/results/dices/" + QSIRECON_SUFFIX
    )
    BUNDLE_NAMES = "/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/data/bundle_names.txt"
    OUTPUT_PATH = (
        "/cbica/projects/clinical_dmri_benchmark/results/discriminability/one_sample_"
        + QSIRECON_SUFFIX
        + ".csv"
    )

    with open(BUNDLE_NAMES, "r") as f:
        bundles = f.read().splitlines()
    for i, bundle in enumerate(bundles):
        bundles[i] = bundle.replace("_", "").replace("-", "")

    get_discrim_one_sample(DICE_ROOT, bundles, OUTPUT_PATH)

