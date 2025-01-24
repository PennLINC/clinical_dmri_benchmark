import os
import re
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

    # Now get only the subject root (no sub-)
    subject_ids_extracted = [re.search(r'sub-(?:NDARINV)?(.*)', sbj).group(1) for sbj in subjects]

    return subject_ids_extracted


def load_masks_as_numpy(qsirecon_root, subject_roots, bundle):
    """
    Loads all masks into memory as NumPy arrays and stores them in a dictionary.

    Args:
      qsirecon_root: Root directory where subject folders are stored.
      subject_roots: List of subject IDs.
      bundle: The specific bundle name for which masks are loaded.

    Returns:
      A dictionary with keys as (subject_id, run) tuples and values as NumPy arrays of masks.
    """
    masks = {}
    for subject_root in subject_roots:
        for session in ["ses-baselineYear1Arm1", "ses-2YearFollowUpYArm1", "ses-04A", "ses-06A"]:
            # if session is baseline or year 2, subject_id = sub-NDARINV{subject_id}, else it's just sub-{subject_id}
            if session in ["ses-baselineYear1Arm1", "ses-2YearFollowUpYArm1"]:
                subject_id = f"sub-NDARINV{subject_root}"
            else:
                subject_id = f"sub-{subject_root}"
            
            mask_path = glob.glob(
                f"{qsirecon_root}/{subject_id}/{session}/dwi/MNI/{subject_id}_{session}*space-MNI152NLin2009cAsym*bundle-{bundle}_mask.nii.gz"
            )[0]
            if mask_path:
                mask_image = sitk.ReadImage(mask_path)
                mask_array = sitk.GetArrayFromImage(mask_image)
                sparse_mask = csr_matrix(mask_array.flatten())
                masks[(subject_root, session)] = sparse_mask
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
    sessions = []
    for id in subject_ids:
        # Add sessions available in "masks" dictionary if they are present
        for session in ["ses-baselineYear1Arm1", "ses-2YearFollowUpYArm1", "ses-04A", "ses-06A"]:
            if (id, session) in masks:
                sbj_ids_duplicated.append(id)
                sessions.append(session)
                sbj_ids_duplicated.append(id)
                sessions.append(session)

    # Initialize dice_array with dimensions based on the number of subject-session combinations
    dice_array = np.zeros([len(sbj_ids_duplicated), len(sbj_ids_duplicated)]) - 1
    indexes_header = []

    # Loop through each subject-session combination
    for i, sbj_session_1 in enumerate(zip(sbj_ids_duplicated, sessions)):
        sbj_id_1 = sbj_session_1[0]
        session_1 = sbj_session_1[1]
        indexes_header.append(f"{sbj_id_1}_{session_1}")
        
        # Check if the subject-session pair exists in masks
        if sbj_session_1 not in masks:
            dice_array[i, :] = np.nan
            continue
        
        mask1 = masks[sbj_session_1]
        for j, sbj_session_2 in enumerate(zip(sbj_ids_duplicated, sessions)):
            if dice_array[i, j] != -1 and dice_array[j, i] != -1:
                continue
            
            if sbj_session_2 not in masks:
                dice_array[i, j] = np.nan
                dice_array[j, i] = np.nan
            else:
                mask2 = masks[sbj_session_2]
                dice_coefficient = dice_coefficient_numpy(mask1, mask2)
                dice_array[i, j] = dice_coefficient
                dice_array[j, i] = dice_coefficient

    # Create a DataFrame for the dice coefficient matrix
    dice_df = pd.DataFrame(dice_array, index=indexes_header, columns=indexes_header)
    #for i in range(dice_array.shape[0]):
    #    dice_df.loc[indexes_header[i]] = dice_array[i, :]
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
        f"/cbica/projects/abcd_qsiprep/bundle_comparison/test_data/qsirecon-{QSIRECON_SUFFIX}"
    )
    EXCLUDED_SBJ_LIST = "/cbica/projects/abcd_qsiprep/bundle_comparison/clinical_dmri_benchmark/analysis/data_processing/subject_lists/excluded_subjects.txt"
    OUTPUT_ROOT = (
        "/cbica/projects/abcd_qsiprep/bundle_comparison/results/dices/"
        + QSIRECON_SUFFIX
    )
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    # Get ids of reconstructed subjects
    sbj_ids = get_subject_ids(ROOT_QSIRECON, EXCLUDED_SBJ_LIST)

    # Preload masks to RAM as NumPy arrays
    masks = load_masks_as_numpy(ROOT_QSIRECON, sbj_ids, BUNDLE_NAME)

    # Calculate Dice scores using preloaded masks
    dice_df = calculate_dice_scores(sbj_ids, masks)

    # save df as csv
    csv_name = os.path.join(OUTPUT_ROOT, BUNDLE_NAME + ".csv")
    dice_df.to_csv(csv_name)
