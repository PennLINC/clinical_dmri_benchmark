#!/usr/bin/env python
import os
import logging
logging.basicConfig(level=logging.INFO)
import json
from get_subject_list import get_completed_subjects, get_available_subjects

RAW_DATA = '/cbica/comp_space/clinical_dmri_benchmark/data/PNC/BIDS'
OUTPUTS_QSIPREP = '/cbica/projects/clinical_dmri_benchmark/results/qsiprep_outputs'

available_subjects = get_available_subjects(RAW_DATA)
preprocessed_subjects = get_completed_subjects(OUTPUTS_QSIPREP, available_subjects)

logging.info(f"Found {len(preprocessed_subjects)} sessions that have been successfully pre-processed.")

with open("preprecessed_subject_list.txt", "w") as fhandle:
    fhandle.write("\n".join(preprocessed_subjects))