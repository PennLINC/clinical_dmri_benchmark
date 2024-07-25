#!/usr/bin/env python
import os
import logging
logging.basicConfig(level=logging.INFO)
import json

RAW_DATA = '/cbica/comp_space/clinical_dmri_benchmark/data/PNC'
OUTPUTS_QSIPREP = '/cbica/projects/clinical_dmri_benchmark/results/qsiprep_outputs/out/qsiprep'

def find_at_least_one(string_list, pattern):
    return any([pattern in item for item in string_list])

def get_completed_subjects(path_to_dwiqc: str):
    """Reads the QC file from the output directory to determine subjects that
    were already pre-processed.

    Args:
      path_to_dwiqc: Path to the QC (qsiprep output 'dwiqc.json) file to be considered.

    Returns:
      List of subjects that have both run-01 and run-02 pre-processed.
    """
    if os.path.exists(path_to_dwiqc) == False:
        logging.info("No qc file found at " + path_to_dwiqc + ". Assuming no subjects have been processed so far.")
        return []

    with open(path_to_dwiqc) as f:
        dwiqc_json = json.load(f)
    qc_data = dwiqc_json['subjects']

    processed_subIDs = []
    for subject in qc_data:
        processed_subIDs.append(subject['participant_id'])
    processed_subIDs.sort()

    # For each subject two runs were acquired. So each subject ID should appear twice in the QC file.
    # If this is not the case, only one run has been processed.
    subIDs_both_runs_processed = []
    for processed_subID in processed_subIDs:
        occurences_subid = processed_subIDs.count(processed_subID)
        if occurences_subid == 2 and processed_subID not in subIDs_both_runs_processed:
            subIDs_both_runs_processed.append(processed_subID)
    
    return subIDs_both_runs_processed

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

completed_subjects = get_completed_subjects(os.path.join(OUTPUTS_QSIPREP, 'dwiqc.json'))
subjects_to_process = get_available_subjects(RAW_DATA)

needs_processing = sorted(set(subjects_to_process) - set(completed_subjects))
logging.info(f"Found {len(needs_processing)} sessions to process")

with open("subject_list.txt", "w") as fhandle:
    fhandle.write("\n".join(needs_processing))