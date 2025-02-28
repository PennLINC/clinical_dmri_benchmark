#! /bin/bash

# Run on juseless
source ~/.venvs/clinical_dmri_benchmark/bin/activate
python3 /data/project/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/prediction/predict_cognition.py $1 $2 $3 $4 $5