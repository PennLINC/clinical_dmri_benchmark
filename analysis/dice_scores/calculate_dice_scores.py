import os
import numpy as np
import pandas as pd
import argparse
import glob
from itertools import combinations
import SimpleITK as sitk
from scipy.sparse import csr_matrix

def get_subject_ids(qsirecon_outputs: str, excluded_subjects: str = None) -> list:
    """Created a python list of all subject folders in a specified qsirecon output directory.
    When provided, excludes subjects that are specified in a txt file of subjects to be excluded.

    Args:
      qsirecon_outputs: Path to a qsirecon output directory containing folders
      for different subjects.
      excluded_subjects: Path to a txt file containig subject ids (one per line)
      that should be excluded from the analysis. Optional, defaults to None.

    Returns:
      Sorted list of subjects ids
    """
    # Get all folders in the specified directory that start with "sub"
    subjects = [
        name
        for name in os.listdir(qsirecon_outputs)
        if os.path.isdir(os.path.join(qsirecon_outputs, name))
        and name.startswith("sub")
    ]

    # Open list of excluded subjects and remove all of them from the list if they exist in the list
    with open(excluded_subjects, "r") as f:
        excluded_subjects = f.read().splitlines()
    for subject in excluded_subjects:
        if subject in subjects:
            subjects.remove(subject)
    subjects.sort()
    return subjects


def load_masks_as_numpy(qsirecon_root, subject_ids, bundle):
    """
    Loads all masks into memory as NumPy arrays and stores them in a dictionary.

    Args:
      qsirecon_root: Root directory where subject folders are stored.
      subject_ids: List of subject IDs.
      bundle: The specific bundle name for which masks are loaded.

    Returns:
      A dictionary with keys as (subject_id, run) tuples and values as NumPy arrays of masks.
    """
    masks = {}
    for subject_id in subject_ids:
        for run in ["run-01", "run-02"]:
            mask_path = glob.glob(
                f"{qsirecon_root}/{subject_id}/ses-PNC1/dwi/MNI/{subject_id}_ses-PNC1*_{run}_space-MNI152NLin2009cAsym_bundle-{bundle}_mask.nii.gz"
            )
            if mask_path:
                mask_image = sitk.ReadImage(mask_path[0])
                mask_array = sitk.GetArrayFromImage(mask_image)
                sparse_mask = csr_matrix(mask_array.flatten())
                masks[(subject_id, run)] = sparse_mask
    return masks


def dice_coefficient_numpy(mask1, mask2):
    """
    Calculate Dice coefficient between two binary masks in NumPy.

    Args:
      mask1: NumPy array for the first mask.
      mask2: NumPy array for the second mask.

    Returns:
      Dice coefficient as a float.
    """
    intersection = mask1.multiply(mask2).count_nonzero()
    sum_masks = mask1.count_nonzero() + mask2.count_nonzero()
    return 2.0 * intersection / sum_masks if sum_masks > 0 else np.nan


def calculate_dice_scores(subject_ids, masks):
    """
    Calculate Dice scores for each pair of masks.

    Args:
      subject_ids: List of subject IDs.
      masks: Dictionary containing preloaded masks with (subject_id, run) as keys.

    Returns:
      A DataFrame containing Dice scores for each pair of masks.
    """
    sbj_ids_duplicated = []
    runs = []
    for id in subject_ids:
        sbj_ids_duplicated.append(id)
        runs.append("run-01")
        sbj_ids_duplicated.append(id)
        runs.append("run-02")

    dice_array = np.zeros([len(subject_ids * 2), len(subject_ids * 2)]) - 1
    indexes_header = []
    for i, sbj_run_1 in enumerate(zip(sbj_ids_duplicated, runs)):
        sbj_id_1 = sbj_run_1[0]
        run_1 = sbj_run_1[1]
        indexes_header.append(sbj_id_1 + "_" + run_1)
        if (sbj_run_1 in masks) == False:
            dice_array[i, :] = np.nan
            continue
        mask1 = masks[sbj_run_1]
        for j, sbj_run_2 in enumerate(zip(sbj_ids_duplicated, runs)):
            if dice_array[i, j] != -1 and dice_array[j, i] != -1:
                continue
            if (sbj_run_2 in masks) == False:
                dice_array[i, j] = np.nan
                dice_array[j, i] = np.nan
            else:
                mask2 = masks[sbj_run_2]
                dice_coefficient = dice_coefficient_numpy(mask1, mask2)
                dice_array[i, j] = dice_coefficient
                dice_array[j, i] = dice_coefficient
    dice_df = pd.DataFrame(index=indexes_header, columns=indexes_header)
    for i in range(dice_array.shape[0]):
        dice_df.loc[indexes_header[i]] = dice_array[i, :]
    return dice_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruction method")
    parser.add_argument(
        "--recon_suffix",
        type=str,
        required=True,
        help="Reconstruction method (e.g., GQIautotrack)",
    )
    parser.add_argument(
        "--bundle",
        type=str,
        required=True,
        help="Name of the bundle considered for dice score calculation",
    )
    args = parser.parse_args()

    QSIRECON_SUFFIX = args.recon_suffix
    BUNDLE_NAME = args.bundle
    ROOT_QSIRECON = (
        "/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/qsirecon-"
        + QSIRECON_SUFFIX
    )
    EXCLUDED_SBJ_LIST = "/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists/excluded_subjects.txt"
    OUTPUT_ROOT = (
        "/cbica/projects/clinical_dmri_benchmark/results/dices/"
        + QSIRECON_SUFFIX
    )

    # Get ids of reconstructed subjects
    sbj_ids = get_subject_ids(ROOT_QSIRECON, EXCLUDED_SBJ_LIST)

    # Preload masks to RAM as NumPy arrays
    masks = load_masks_as_numpy(ROOT_QSIRECON, sbj_ids, BUNDLE_NAME)

    # Calculate Dice scores using preloaded masks
    dice_df = calculate_dice_scores(sbj_ids, masks)

    # save df as csv
    csv_name = os.path.join(OUTPUT_ROOT, BUNDLE_NAME + ".csv")
    dice_df.to_csv(csv_name)
