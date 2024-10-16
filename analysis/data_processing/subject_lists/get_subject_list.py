#!/usr/bin/env python
import os
import logging
logging.basicConfig(level=logging.INFO)
import json

RAW_DATA = '/cbica/comp_space/clinical_dmri_benchmark/data/PNC/BIDS'
OUTPUTS_QSIPREP = '/cbica/projects/clinical_dmri_benchmark/results/qsiprep_outputs'

def find_at_least_one(string_list, pattern):
    return any([pattern in item for item in string_list])

def get_completed_subjects(qsiprep_outputs: str, available_subjects: list):
    """Iterate over the list of available subjects.
	If a folder for this subject exists in the output directory and there is
	no folder for this subject in the directory of failed subjects we assume the subject
	has been successfully pre-processed.

    Args:
      qsiprep_outputs: Path to folder containing all qsiprep outputs
      available_subjects: List of all subjects that have the data necessary for pre-processing

    Returns:
      List of subjects that have already been pre-processed.
    """
    if os.path.exists(qsiprep_outputs) == False:
        logging.info("No output folder found at " + qsiprep_outputs + ". Assuming no subjects have been processed so far.")
        return []

    processed_subIDs = []
    for subject in available_subjects:
        subject_in_outputs = os.path.exists(os.path.join(qsiprep_outputs, subject))
        subject_in_failures = os.path.exists(os.path.join(qsiprep_outputs, 'failures', subject))
        if (subject_in_outputs == True) and (subject_in_failures == False):
            processed_subIDs.append(subject)
    processed_subIDs.sort()
    
    return processed_subIDs

def get_available_subjects(data_dir: str):
    """Checks which subjects have all necessary data for pre-processing available.

    Args:
      data_dir: Directory containing subject folders in BIDS format.

    Returns:
      List of subjects which can be pre-processed with QSIprep.
    """
    data_dir_content = os.listdir(data_dir)
    data_dir_folders = [entry for entry in data_dir_content if not os.path.isdir(entry)]
    subject_folders = [folder for folder in data_dir_folders if folder.startswith('sub-')]

    available_subjects = []
    for subject_folder in subject_folders:
        if check_for_mandatory_files(os.path.join(data_dir, subject_folder)) == True:
            available_subjects.append(subject_folder)
    return available_subjects

def check_for_mandatory_files(subject_folder: str):
    """Check for necessary files (here, two DWI runs and T1w).
    Exit early if any are missing.
    
    Args:
     subject_folder: Path to the currently considered subject folder
    
    Returns:
     True if all file available, else False
    """
    anat_path = os.path.join(RAW_DATA, subject_folder, 'ses-PNC1', 'anat')
    dwi_path = os.path.join(RAW_DATA, subject_folder, 'ses-PNC1', 'dwi')

    # first check if folders exist
    if os.path.isdir(anat_path) == False:
        return False
    if os.path.isdir(dwi_path) == False:
        return False
    
    # In case the folder exists, get file names and check for completeness
    anat_data = os.listdir(anat_path)
    dwi_data = os.listdir(dwi_path)

    if find_at_least_one(anat_data, '_T1w.json') and find_at_least_one(anat_data, '_T1w.nii.gz'):
        anat_complete = True
    else:
        return False

    required_dwi_data = ['_run-01_dwi.bval', '_run-01_dwi.bvec', '_run-01_dwi.nii.gz', '_run-01_dwi.json',
                         '_run-02_dwi.bval', '_run-02_dwi.bvec', '_run-02_dwi.nii.gz', '_run-02_dwi.json']
    for required_file in required_dwi_data:
        if find_at_least_one(dwi_data, required_file):
            dwi_complete = True
        else:
            return False
    
    return True

if __name__ == '__main__':
    subjects_to_process = get_available_subjects(RAW_DATA)
    completed_subjects = get_completed_subjects(OUTPUTS_QSIPREP, subjects_to_process)

    needs_processing = sorted(set(subjects_to_process) - set(completed_subjects))
    logging.info(f"Found {len(needs_processing)} sessions to process")

    with open("subject_list.txt", "w") as fhandle:
        fhandle.write("\n".join(needs_processing))
