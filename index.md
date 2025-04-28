---
layout: default
title: ""
description: ""
parent: Documentation
has_children: false
has_toc: false
nav_order: 3
---


# Benchmarking Reconstruction Methods for Bundle Segmentation: Preparing for Clinical Translation

Acquiring high-quality multi-shell neuroimaging diffusion MRI (dMRI) datasets is time- and resource-intensive. dMRI scans from healthcare systems are usually single-shelled and have a lower angular resolution. While they may offer a valuable, large-scale complement to research datasets, the reliability of white matter bundle segmentation and characterization from these scans remains unclear. Here, we leverage a large research dataset where each 64-direction dMRI scan was acquired as two independent 32-direction runs per subject. Notably, these two 32-direction scans have a quite similar acquisition scheme to clinically feasible scans.  To investigate how recently developed bundle segmentation methods generalize to this data, we evaluated the test-retest reliability of white matter (WM) bundle extraction across three orientation distribution function (ODF) reconstruction methods: generalized q-sampling imaging (GQI), constrained spherical deconvolution (CSD), and single-shell three-tissue CSD (SS3T). We found that the majority of WM bundles could be reliably extracted from dMRI scans that were acquired using the 32-direction, single shell acquisition scheme. The mean dice coefficient of reconstructed WM bundles was consistently higher within-subject than between-subject for all WM bundles and reconstruction methods, illustrating high reconstruction reliability. Further, when leveraging features of the reconstructed bundles to predict a complex reasoning score, we observed stable prediction accuracies of r between 0.15-0.36. Among the three reconstruction methods, SS3T had the best balance between sensitivity and specificity, with high intra-class correlation of extracted features, more plausible bundles, and strong predictive performance. More broadly, these results demonstrate that bundle segmentation can achieve robust performance even on lower angular resolution, single-shell dMRI, with particular advantages for ODF methods optimized for single-shell data. This highlights the enormous research potential for dMRI collected in healthcare settings.

# I. Project Information

## Project Team 
**Project Lead:** Amelie Rauland

**Faculty Leads:** Matthew Cieslak and Theodore D. Satterthwaite

**Analytic Replicator:** Steven L. Meisler

**Collaborators:**
<br>
Aaron Alexander-Bloch, Joëlle Bagautdinova, Erica B. Baller, Ruben C. Gur, Raquel E. Gur, Audrey C. Luo, Tyler M. Moore, Oleksandr V. Popovych, Kathrin Reetz, David Roalf, Valerie J. Sydnor, Simon B. Eickhoff

## Project Timeline
**Project Start Date:** 06/2024
<br>
**Current Project Status:** In preparation

## Dataset
Philadelphia Neurodevelopmental Cohort (PNC)

## Code and Communication
**Github repo:** [https://github.com/PennLINC/clinical_dmri_benchmark/tree/main](https://github.com/PennLINC/clinical_dmri_benchmark/tree/main)
<br>
**Slack Channel:** #clinical_dmri_benchmark

<!-- ### Current work products

I.e., citations to poster presentations, links to preprints, final publication citation -->

# II. CUBIC Project Directory Structure
The project directory on CUBIC is `/cbica/projects/clinical_dmri_benchmark`. The following directories are relative to this home directory if not specified otherwise.

| **Directory**                                        | **Description**                                                                                                                              |
|------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `~/clinical_dmri_benchmark`                          | GitHub repo                                                   |
| `~/clinical_dmri_benchmark/analysis`                          | GitHub repo: Code for data processing, analysis and figure plotting divided into sub-folders                                                                                |
| `~/clinical_dmri_benchmark/data`                          | GitHub repo: data used by several scripts in the repo (e.g. bundle names)                                                                                |
| `~/clinical_dmri_benchmark/figures`                          | GitHub repo: Figures produced by code in the `analysis` folder                   |
| `~/clinical_dmri_benchmark/software`                          | GitHub repo: Requirement files for python environments                  |
| `~/images`                                           | Singularity images for qsiprep and qsirecon                                                                                                  |
| `~/results`                                          | Outputs of data processing and analysis (sub-folders for different steps of the analysis: pre-processing, reconstruction, dice scores, etc.) |
| `~/data`                                             | Additional data needed for analysis that is too large to be stored in the GitHub repo, can't be shared publicly, or can be easily downloaded and therefore doesn't need to be shared through the repo  (e.g. atlas bundles, QC files, prediction confounds and targets)                                         |
| `/cbica/comp_space/`<br>`clinical_dmri_benchmark/PNC/BIDS` | Raw PNC data (downloaded and cloned using datalad)                                                                                           |
| `/cbica/comp_space/`<br>`clinical_dmri_benchmark/MNI`      | Reference T1w MNI image                                                                                                                      |

# III. Code Documentation
# Software and Data
## 1 Install required software and setup python environment
### 1.1 Singularity images for qsiprep and qsirecon
QSIPrep: `apptainer build qsiprep-0.21.4.sif docker://pennlinc/qsiprep:0.21.4`
<br>
QSIRecon: `apptainer build qsirecon-0.23.2.sif docker://pennlinc/qsirecon:0.23.2`

### 1.2 Setup `clinical_dmri_benchmark` python environment
This is the main environment used in this analysis.
<br>
Micromamba:
`micromamba create -n clinical_dmri_benchmark --file ~/software/cdbm_environment.yml`
<br>
For prediction, the analysis was run on another cluster where it was more straight forward to use a python `venv`:
```
curl -LsSf https://astral.sh/uv/install.sh | sh 
uv venv --python 3.12.5 .venvs/clinical_dmri_benchmark 
source .venvs/clinical_dmri_benchmark/bin/activate 
uv pip install -r ~/software/cdbm_environment.txt
```

### 1.3 Setup mayavi python environment
This environment was only used to plot the the population maps over the atlas bundles.
`micromamba create -n mayavi --file /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/software/mayavi_environment.yml`

## 2 Get PNC data in BIDS format
The raw PNC data in BIDS format was stored at    `/cbica/comp_space/clinical_dmri_benchmark/PNC/BIDS` . 
<br>
Clone the dataset from PMACs as described [here](https://pennlinc.github.io/docs/DataWorkflows/FetchingYourPMACSData/). When using `datalad get` , it is only necessary to get the T1w images (`*_T1w.json` , `*_T1w.nii.gz` ) and the diffusion data (`*_dwi.bval`, `*_dwi.bvec,` `*_dwi.nii.gz,` `*_dwi.json`).
<br>
<br>
The MNI reference image from QSIPrep was stored at `/cbica/comp_space/clinical_dmri_benchmark/PNC/MNI/mni_1mm_t1w_lps_brain.nii.gz`. It can be downloaded from [here](https://github.com/PennLINC/qsiprep/blob/0.21.4/qsiprep/data/mni_1mm_t1w_lps_brain.nii.gz).

# Data Processing
## 3 Pre-process the data using QSIPrep
### 3.1 Get subject list for pre-processing
```
micromamba activate clinical_dmri_benchmark
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists
python3 get_subject_list.py
```
→ This creates a list of all subjects with two dMRI scans and a T1w scan that have not been pre-processed yet

### 3.2 Run pre-processing
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing
sbatch PNC_qsiprep.sh
```

## 4 Reconstruct WM bundles using three different ODF reconstructions with QSIRecon

### 4.1 GQI
**4.1.1 Get subject list for GQIautotrack reconstruction**
```
micromamba activate clinical_dmri_benchmark
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists
python3 get_preprocessed_subject_list.py --recon_suffix GQIautotrack
```
This creates a list of subjects that have been pre-processed and not yet reconstructed using GQI.

**4.1.2 Run autotrack based on GQI reconstruction (default)**
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing
sbatch PNC_qsirecon_gqi_autotrack.sh
```

### 4.2 CSD and SS3T
The reconstruction using CSD and SS3T is run in two steps: First we reconstruct the ODFs using CSD / SS3T in QSIRecon and then we run Autotrack in DSIStudio based on the CSD / SS3T ODFs.

**4.2.1 Get subject lists for ODF reconstruction**
```
micromamba activate clinical_dmri_benchmark
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists
python3 get_preprocessed_subject_list.py --recon_suffix CSD
python3 get_preprocessed_subject_list.py --recon_suffix SS3T
```
This creates a list of subjects that have been pre-processed and not yet reconstructed using CSD / SS3T.

**4.2.2 Run ODF reconstruction**
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing
sbatch PNC_qsirecon_csd.sh
sbatch PNC_qsirecon_ss3t.sh
```

**4.2.3 Get subject lists for bundle reconstruction**
```
micromamba activate clinical_dmri_benchmark
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists
python3 get_preprocessed_subject_list.py --recon_suffix CSDautotrack
python3 get_preprocessed_subject_list.py --recon_suffix SS3Tautotrack
```
This creates a list of subjects that have been pre-processed and not yet reconstructed using CSDautotrack / SS3Tautotrack.

**4.2.4 Run autotrack based on CSD / SS3T reconstruction:**
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing
sbatch PNC_qsirecon_csd_autotrack.sh
sbatch PNC_qsirecon_ss3t_autotrack.sh
```

## 5 Warp reconstructed bundles to MNI space and mask

### 5.1 Get subject lists
```
micromamba activate clinical_dmri_benchmark
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists
python3 get_reconstructed_subject_list.py --recon_suffix GQIautotrack
python3 get_reconstructed_subject_list.py --recon_suffix CSDautotrack
python3 get_reconstructed_subject_list.py --recon_suffix SS3Tautotrack
```
This creates a subject list of all subjects that have been reconstructed but not yet warped and masked for each of the reconstruction methods.

### 5.2 Warp bundles to MNI space and create binary mask
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing
sbatch warp_bundles_to_mni_and_mask.sh GQIautotrack
sbatch warp_bundles_to_mni_and_mask.sh CSDautotrack
sbatch warp_bundles_to_mni_and_mask.sh SS3Tautotrack
```

## 6 Create list of excluded subjects
```
micromamba activate clinical_dmri_benchmark
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists
python3 qc.py
```
This list checks for subjects with acquisition variants, subjects that could not be pre-processed or reconstructed and subjects that failed QC based on Roalf et al., 2016.

# Bundle Reliability Analysis
## 7 Reconstruction Fractions
### 7.1 Determine fractions of reconstructed bundles
```
micromamba activate clinical_dmri_benchmark
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/fractions_reconstructed_bundles
python3 get_reconstructed_bundles.py --recon_suffix GQIautotrack
python3 get_reconstructed_bundles.py --recon_suffix CSDautotrack
python3 get_reconstructed_bundles.py --recon_suffix SS3Tautotrack
```

### 7.2 Plot the fractions 🎨
This notebook was run locally and the following files had to be moved to the local setup:
- `/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/reconstructed_bundles_GQIautotrack.csv`
- `/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/reconstructed_bundles_CSDautotrack.csv`
- `/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/reconstructed_bundles_SS3Tautotrack.csv` <br>

Adjust `CSV_ROOT` at the top of the script to where you saved the required files and run `<GIT_REPO_HOME>/analysis/fractions_reconstructed_bundles/plot_recon_fractions.ipynb` to create the plot of reconstruction fractions.

## 8 Dice Scores

### 8.1 Calculate dice scores
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/dice_scores
sbatch calculate_dice_scores.sh GQIautotrack
sbatch calculate_dice_scores.sh CSDautotrack
sbatch calculate_dice_scores.sh SS3Tautotrack
```

### 8.2 Plot full distributions 🎨
This script was run locally and requires the csv files containing the dice scores between any two scans to be moved to local from `/cbica/projects/clinical_dmri_benchmark/results/dices`. Adjust `DICE_ROOT` at the top of the script to where you saved the required files on the local setup. This is also where the high quality versions of the files are saved to as they are too large to be saved in the GitHub repo.
```
micromamba activate clinical_dmri_benchmark
python3 <GIT_REPO_HOME>/analysis/dice_scores/plot_full_dice_distributions.py
```
The reconstruction method needs to be set at the top of the script as `GQI` , `CSD`  or `SS3T` .

### 8.3 Plot median distributions 🎨
As above, this notebook was also run locally and requires the files from `/cbica/projects/clinical_dmri_benchmark/results/dices`. The `DICE_ROOT` at the top of the notbeook needs to be adjusted to where the files were saved locally.
Run `<GIT_REPO_HOME>/analysis/dice_scores/plot_median_dice_scores.ipynb` to plot the median (median within and between dice score per bundle) distributions for all reconstruction methods.

## 9 Discriminability

### 9.1 Calculate discriminability
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/discriminability
sbatch discrim_two_sample_filtered.sh GQIautotrack CSDautotrack SS3Tautotrack
sbatch discrim_two_sample_filtered.sh GQIautotrack SS3Tautotrack CSDautotrack
sbatch discrim_two_sample_filtered.sh CSDautotrack SS3Tautotrack GQIautotrack
```
Calculation of discriminability and determination of significant differences will be perfromed for the first two arguments, the third argument is passed to perform the filtering and only include scans for which a given bundle was reconstructed for all three methods.

### 9.2 Plot discriminability 🎨
The notebook was run locally and the following files had to be moved to local to run the code:
- `/cbica/projects/clinical_dmri_benchmark/results/discriminability/two_sample_GQIautotrack_CSDautotrack.csv`
- `/cbica/projects/clinical_dmri_benchmark/results/discriminability/two_sample_CSDautotrack_SS3Tautotrack.csv`
- `/cbica/projects/clinical_dmri_benchmark/results/discriminability/two_sample_GQIautotrack_SS3Tautotrack.csv` <br>

Adjust `DISCRIM_CSV_ROOT` at the top of the script with where you saved the required files on the local setup. This is also where a merged csv will be saved.
<br>
Run `<GIT_REPO_HOME>/analysis/discriminability/plot_discrim_two_sample.ipynb` to create the plot comparing discriminability between reconstruction methods for all reconstructed WM bundles.

## 10 Bundle Completeness
### 10.1 Calculate population maps
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/overlay_maps
sbatch calculate_overlay_maps.sh GQIautotrack
sbatch calculate_overlay_maps.sh CSDautotrack
sbatch calculate_overlay_maps.sh SS3Tautotrack
```

### 10.2 Extract atlas bundles from DSIStudio
- [Install DSI Studio Hou](https://dsi-studio.labsolver.org/download.html)
- Download high-resolution HCP1065 1mm fib file from https://brain.labsolver.org/hcp_template.html and open it in DSIStudio. In the project directory this file can be found here: `/cbica/projects/clinical_dmri_benchmark/data/HCP1065.1mm.fib.gz`
- Right-click DSIStudio installation and select `Show Package Contents` .
- Then open `/Applications/dsi_studio.app/Contents/MacOS/atlas/human/human.tt.gz` in DSIStudio on top of the HCP fib file.
- Now merge all WM bundles that have two underscores in the name to their parent bundle. E.g. `ProjectionBrainstem_CorticopontineTractR_Frontal` + `ProjectionBrainstem_CorticopontineTractR_Parietal` + `ProjectionBrainstem_CorticopontineTractR_Occipital` → `ProjectionBrainstem_CorticopontineTractR`
- Then select all bundles except for the Cerebellum and Cranial Nerves, right-click one of them and select `save all tracts as multiple files`
- These files should then be moved to `/cbica/projects/clinical_dmri_benchmark/data/atlas_bundles/.`

### 10.3 Mask atlas bundles and warp to MNIc space
First, get T1w images from MNIb and MNIc space from template flow using datalad. These should be saved here:
- `/cbica/projects/clinical_dmri_benchmark/data/templateflow/tpl-MNI152NLin2009bAsym/tpl-MNI152NLin2009bAsym_res-1_T1w.nii.gz`
- `/cbica/projects/clinical_dmri_benchmark/data/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz`<br>

```
# Calculate transform using the two T1w images by running
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/overlap
sbatch calculate_transform_mnib2c.sh # This code is largely based on code by Steven Meisler.
# Mask and transform all atlas bundles
bash mask_and_warp_atlas_bundles.sh
```

### 10.4 Plot population maps over atlas bundles 🎨
The code for plotting is largely based on code by Matthew Cieslak.

The script requires it’s own python environment and needs to be run somewhere with visual output! Here, the script was run on a local laptop. The following files are required:
- Atlas bundles in MNI space: Copy from `/cbica/projects/clinical_dmri_benchmark/data/atlas_bundles`
- Population maps: Copy from `/cbica/projects/clinical_dmri_benchmark/results/overlay_maps`
- MNI reference image: Download from [QSIPrep GitHub repo](https://github.com/PennLINC/qsiprep/blob/0.21.4/qsiprep/data/mni_1mm_t1w_lps_brain.nii.gz).
- Surfaces: Download from [neuromaps](https://osf.io/dv28y). <br>

To run the code:
- Activate environment in terminal: `micromamba activate myavi`
- Start interactive python session in terminal with `ipython --gui=qt5`
- Run code from `<GIT_REPO_HOME>/analysis/overlay_maps/plot_population_map_on_atlas.py` in interactive python session to create the plots.

### 10.5 Calculate sensitivity and specificity of reconstructed bundles with atlas bundles
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/overlap
sbatch sensitivity_specificity.sh GQIautotrack
sbatch sensitivity_specificity.sh CSDautotrack
sbatch sensitivity_specificity.sh SS3Tautotrack
```
This code is largely based on code by Valerie Sydnor.

### 10.6 Plot sensitivity and specificity 🎨
The notebook was run locally. The following files need to be copied to local for the code to run:
- `/cbica/projects/clinical_dmri_benchmark/results/overlap/GQIautotrack_overlap.csv`
- `/cbica/projects/clinical_dmri_benchmark/results/overlap/CSDautotrack_overlap.csv`
- `/cbica/projects/clinical_dmri_benchmark/results/overlap/SS3Tautotrack_overlap.csv` <br>

Adjust `OVERLAP_ROOT` at the top of the notebook to where you saved the required files locally and run `<GIT_REPO_HOME>/analysis/overlap/plot_sensitivity_specificity.ipynb` to create the plots of sensitivity and specificity. The overall median plot will be saved in the GitHub repo, the separate plots for each of the bundle will be saved at `OVERLAP_ROOT`.

# Prediction Analysis
CSVs for confounds and targets can be found at `/cbica/projects/clinical_dmri_benchmark/data/prediction` on CUBIC.

## 11 Prepare Data

### 11.1 Prepare feature csvs
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/prediction/prep_prediction_files
micromamba activate clinical_dmri_benchmark
# Move bundle from separate subject folders to common space for easier processing
bash move_bundle_stats.sh GQIautotrack
bash move_bundle_stats.sh CSDautotrack
bash move_bundle_stats.sh SS3Tautotrack
# Create feature CSVs
python3 create_feature_csvs.py
```

### 11.2 Calculate and plot feature ICCs 🎨
This notebook was run locally. The following files are required and need to be moved to the local setup:
<br> `/cbica/projects/clinical_dmri_benchmark/results/bundle_stats/<reconstruction>autotrack_<run>.csv`, with `<reconstruction>` in [GQI, CSD, SS3T] and `<run>` in [run-01, run-02].

Adjust the `BUNDLE_STATS_ROOT` at the top of the notebook to where the files were saved locally and run `<GIT_REPO_HOME>/analysis/prediction/plot_feature_icc.ipynb`. 
<br>
Adjust the `FEATURE_OF_INTEREST` variable to `total_volume_mm3` , `dti_fa` and `md` to create the plots for all three features.

### 11.3 Prepare confound csv
```
cd /cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/prediction/prep_prediction_files
micromamba activate clinical_dmri_benchmark
python3 prepare_confounds_csv.py
```
The script extracts the head movement for all scans and creates one confound csv containing all confounds of interest for all subjects.

## 12 Run Prediction
Prediction was run on a different system. Following files need to be moved to the other cluster to run the prediction:
- Confounds: `/cbica/projects/clinical_dmri_benchmark/data/prediction/confounds/confounds.csv`
- ID conversion: `/cbica/projects/clinical_dmri_benchmark/data/QC/bblid_scanid_sub.csv`
- Features: `/cbica/projects/clinical_dmri_benchmark/results/bundle_stats/<reconstruction>_<run>.csv`
- Targets: `/cbica/projects/clinical_dmri_benchmark/data/prediction/targets/n9498_cnb_zscores_all_fr_20161215.csv`

The prediction performed in the main analysis can be run by submitting `<GIT_REPO_HOME>/analysis/prediction/predict_cognition.submit` to the cluster.

- To perform the supplementary analysis including TBV as a confound replace all instances of `sex,ageAtScan1,mean_fd` with `sex,ageAtScan1,mean_fd,mprage_antsCT_vol_TBV` in the submit file.
- To perform the supplementary analysis for predicting two additional cognitive traits replace all instances of `cpxresAZv2` with either `exeAZv2` or `ciqAZv2` .

The results were copied to CUBIC and can be found at `/cbica/projects/clinical_dmri_benchmark/results/prediction/remove_confounds_features`

## 13 Compare Prediction Model Performances
This script was run locally and requires the prediction result csvs from `/cbica/projects/clinical_dmri_benchmark/results/prediction/remove_confounds_features`.
<br>
Adjust the `RESULT_ROOT` at the top of the notebook to where you saved the prediction results on the local setup and run `<GIT_REPO_HOME>/analysis/prediction/compare_model_performances.py` to obtain a csv with p-values that imply if there is a significant difference between two considered models.
<br>
The resulting output csv with the corrected p-values will be saved under the `RESULT_ROOT`.

## 14 Plot Prediction Results

### 14.1 Plot prediction accuracy 🎨
This notbook was run locally and requires the prediction result csvs from `/cbica/projects/clinical_dmri_benchmark/results/prediction/remove_confounds_features`.
<br>
Adjust the `RESULT_ROOT` at the top of the notebook to where you saved the prediction results on the local setup and run `<GIT_REPO_HOME>/analysis/prediction/plot_prediction_results.ipynb` to plot the prediction accuracy for the main analysis.

- To plot results for the supplementary analysis including TBV as a confound, set `TBV_AS_CONFOUND = True` at the beginning of the script.
- To plot results for the supplementary analysis for the two additional cognition targets set `TARGET = "exeAZv2"` or `TARGET = "ciqAZv2"` at the beginning of the script.

### 14.2 Plot prediction similarity 🎨
This notbook was run locally and requires the prediction inspector csvs from `/cbica/projects/clinical_dmri_benchmark/results/prediction/remove_confounds_features`.
<br>
Adjust the `RESULT_ROOT` at the top of the notebook to where you saved the prediction results on the local setup and run `<GIT_REPO_HOME>/analysis/prediction/plot_prediction_reliability.ipynb` to plot the similarity between prediction from different scans for the main analysis.

- To plot results for the supplementary analysis including TBV as a confound, set `TBV_AS_CONFOUND = True` at the beginning of the script.
- To plot results for the supplementary analysis for the two additional cognition targets set `TARGET = "exeAZv2"` or `TARGET = "ciqAZv2"` at the beginning of the script.