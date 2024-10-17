#!/usr/bin/env python
import os
import logging
logging.basicConfig(level=logging.INFO)
import json
from get_subject_list import get_completed_subjects, get_available_subjects
import argparse

# Setup argument parser
parser = argparse.ArgumentParser(description="Reconstruction method")
parser.add_argument('--recon_suffix', type=str, required=True, help='Reconstruction method (e.g., GQIautotrack)')
args = parser.parse_args()

QSIRECON_SUFFIX = args.recon_suffix
RAW_DATA = '/cbica/comp_space/clinical_dmri_benchmark/data/PNC/BIDS'
OUTPUTS_QSIPREP = '/cbica/projects/clinical_dmri_benchmark/results/qsiprep_outputs'
OUTPUTS_QSIRECON = '/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs'

def get_reconstructed_subjects(qsirecon_outputs: str, preprocessed_subjects: list, qsirecon_suffix: str):
    """Iterate over the list of preprocessed subjects.
      If a folder for this subject exists in the output directory and there is
      no folder for this subject in the directory of failed subjects we assume the subject
      has been successfully pre-processed.

    Args:
      qsirecon_outputs: Path to folder containing all qsirecon outputs
      preprocessed_subjects: List of all subjects that have been successfully pre-processed by qsiprep
      qsirecon_suffix: qsirecon suffix to specifiy which reconstruction method we are checking.
      Should be one of 'GQIautotrack', 'SS3Tautotrack', 'CSDautotrack', 'SS3T', 'CSD'

    Returns:
      List of subjects that have already been reconstructed with the specified reconstruction method.
    """
    qsirecon_suffix_options = ['GQIautotrack', 'SS3Tautotrack', 'CSDautotrack', 'SS3T', 'CSD']
    assert qsirecon_suffix in qsirecon_suffix_options, f"Error: {qsirecon_suffix} is not a valid option."
    full_path_qsirecon_outputs = os.path.join(qsirecon_outputs, 'qsirecon-' + qsirecon_suffix)

    if os.path.exists(full_path_qsirecon_outputs) == False:
        logging.info("No output folder found at " + full_path_qsirecon_outputs + ". Assuming no subjects have been reconstructed so far.")
        return []

    reconstructed_subIDs = []
    for subject in available_subjects:
        subject_in_outputs = os.path.exists(os.path.join(full_path_qsirecon_outputs, subject))
        subject_in_failures = os.path.exists(os.path.join(full_path_qsirecon_outputs, 'failures', subject))
        if (subject_in_outputs == True) and (subject_in_failures == False):
            reconstructed_subIDs.append(subject)
    reconstructed_subIDs.sort()

    return reconstructed_subIDs

available_subjects = get_available_subjects(RAW_DATA)
preprocessed_subjects = get_completed_subjects(OUTPUTS_QSIPREP, available_subjects)
reconstructed_subjects = get_reconstructed_subjects(OUTPUTS_QSIRECON, preprocessed_subjects, QSIRECON_SUFFIX)

needs_reconstruction = sorted(set(preprocessed_subjects) - set(reconstructed_subjects))

logging.info(f"Found {len(needs_reconstruction)} sessions that have been successfully pre-processed and not yet reconstructed using {QSIRECON_SUFFIX}.")

with open("preprocessed_subject_list_" + QSIRECON_SUFFIX  + ".txt", "w") as fhandle:
    fhandle.write("\n".join(needs_reconstruction))
