#!/usr/bin/env python
import os
import logging

logging.basicConfig(level=logging.INFO)
import argparse


def get_reconstructed_subjects(qsirecon_outputs: str, qsirecon_suffix: str):
    """
    Returns a list of all subject ids that have been reconstructed with
    the speficified method but not yet warped to MNI space

    Args:
      qsirecon_outputs: Path to folder containing all qsirecon outputs
      qsirecon_suffix: qsirecon suffix to specifiy which reconstruction method we are checking.
      Should be one of 'GQIautotrack', 'SS3Tautotrack', 'CSDautotrack', 'SS3T', 'CSD'

    Returns:
      List of subjects that have already been reconstructed with the specified reconstruction method
      but not yet warped to MNI space.
    """
    qsirecon_suffix_options = [
        "GQIautotrack",
        "SS3Tautotrack",
        "CSDautotrack",
        "SS3T",
        "CSD",
    ]
    assert (
        qsirecon_suffix in qsirecon_suffix_options
    ), f"Error: {qsirecon_suffix} is not a valid option."
    full_path_qsirecon_outputs = os.path.join(
        qsirecon_outputs, "qsirecon-" + qsirecon_suffix
    )

    if os.path.exists(full_path_qsirecon_outputs) == False:
        logging.info(
            "No output folder found at "
            + full_path_qsirecon_outputs
            + ". Assuming no subjects have been reconstructed so far."
        )
        return []

    reconstructed_subIDs = [
        f
        for f in os.listdir(full_path_qsirecon_outputs)
        if os.path.isdir(os.path.join(full_path_qsirecon_outputs, f))
    ]

    if "failures" in reconstructed_subIDs:
        reconstructed_subIDs.remove("failures")

    reconstructed_subIDs = [
        subid for subid in reconstructed_subIDs
        if not os.path.exists(os.path.join(full_path_qsirecon_outputs, subid, "ses-PNC1", "dwi", "MNI"))
    ]

    return reconstructed_subIDs


# Setup argument parser
parser = argparse.ArgumentParser(description="Reconstruction method")
parser.add_argument(
    "--recon_suffix",
    type=str,
    required=True,
    help="Reconstruction method (e.g., GQIautotrack)",
)
args = parser.parse_args()

QSIRECON_SUFFIX = args.recon_suffix
OUTPUTS_QSIRECON = "/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs"


reconstructed_subjects = get_reconstructed_subjects(
    OUTPUTS_QSIRECON, QSIRECON_SUFFIX
)


logging.info(
    f"Found {len(reconstructed_subjects)} sessions that have been successfully reconstructed and not yet warped using {QSIRECON_SUFFIX}."
)

with open("reconstructed_subject_list_" + QSIRECON_SUFFIX + ".txt", "w") as fhandle:
    fhandle.write("\n".join(reconstructed_subjects))
