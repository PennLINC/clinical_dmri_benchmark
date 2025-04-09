---
layout: default
title: Project Template
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
| `~/clinical_dmri_benchmark`                          | Github repro: Code for data processing, analysis and figures                                                                                 |
| `~/images`                                           | Singularity images for qsiprep and qsirecon                                                                                                  |
| `~/results`                                          | Outputs of data processing and analysis (sub-folders for different steps of the analysis: pre-processing, reconstruction, dice scores, etc.) |
| `~/data`                                             | Additional data needed for analysis (e.g. atlas bundles, QC files, prediction confounds and targets)                                         |
| `/cbica/comp_space/clinical_dmri_benchmark/PNC/BIDS` | Raw PNC data (downloaded and cloned using datalad)                                                                                           |
| `/cbica/comp_space/clinical_dmri_benchmark/MNI`      | Reference T1w MNI image                                                                                                                      |

# III. Code Documentation
# Software and Data
## 1: Install required software and setup python environment
### 1.1: Singularity images for qsiprep and qsirecon
<br>
QSIPrep: `apptainer build qsiprep-0.21.4.sif docker://pennlinc/qsiprep:0.21.4`
<br>
QSIRecon: `apptainer build qsirecon-0.23.2.sif docker://pennlinc/qsirecon:0.23.2`

### 1.2: Setup `clinical_dmri_benchmark` python environment
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

### 1.3: Setup mayavi python environment
This environment was only used to plot the the population maps over the atlas bundles.
`micromamba create -n mayavi --file ~/software/mayavi_environment.yml`

## 2: Get PNC data in BIDS format
The raw PNC data in BIDS format was stored at    `/cbica/comp_space/clinical_dmri_benchmark/PNC/BIDS` . 
<br>
Clone the dataset from PMACs as described [here](https://pennlinc.github.io/docs/DataWorkflows/FetchingYourPMACSData/). When using `datalad get` , it is only necessary to get the T1w images (`*_T1w.json` , `*_T1w.nii.gz` ) and the diffusion data (`*_dwi.bval`, `*_dwi.bvec,` `*_dwi.nii.gz,` `*_dwi.json`).

# Data Processing
## 3: Pre-process the data using QSIPrep
### 3.1: Get subject list for pre-processing
Run `~/analysis/data_processing/subject_lists/get_subject_list.py`.
<br>
→ This creates a list of all subjects with two dMRI scans and a T1w scan that have not been pre-processed yet

### 3.2: Run pre-processing
Run `~/analysis/data_processing/PNC_qsiprep.sh`

## 4: Reconstruct WM bundles using three different ODF reconstructions with QSIRecon

### 4.1: GQI
**4.1.1: Get subject list for GQIautotrack reconstruction**
Run `~/analysis/data_processing/subject_lists/get_preprocessed_subject_list.py --recon_suffix GQIautotrack` to obtain a list of subjects that has been pre-processed and not yet reconstructed using GQI

**4.1.2: Run autotrack based on GQI reconstruction (default)**
<br>
Run `~/analysis/data_processing/PNC_qsirecon_gqi_autotrack.sh`

### 4.2: CSD

The reconstruction using CSD is run in two steps: First we reconstruct the ODFs using CSD in QSIPrep and then we run Autotrack in DSIStudio based on the CSD ODFs.

**4.2.1: Get subject list for CSD reconstruction**
<br>
Run `~/analysis/data_processing/subject_lists/get_preprocessed_subject_list.py --recon_suffix CSD` to obtain a list of subjects that has been pre-processed and not yet reconstructed using CSD

**4.2.2: Run CSD ODF reconstruction**
<br>
Run `~/analysis/data_processing/PNC_qsirecon_csd.sh` 

**4.2.3: Get subject list for CSDautotrack reconstruction**
<br>
Run `~/analysis/data_processing/subject_lists/get_preprocessed_subject_list.py --recon_suffix CSDautotrack` to obtain a list of subjects that has been pre-processed and not yet reconstructed using CSDautotrack

**4.2.4: Run autotrack based on CSD reconstruction:**
<br>
Run `~/analysis/data_processing/PNC_qsirecon_csd_autotrack.sh` 

### 4.3: SS3T
For reconstructing WM bundles based on SS3T ODFs we run the same two steps as for CSD.

**4.3.1: Get subject list for SS3T reconstruction** <br>
Run `~/analysis/data_processing/subject_lists/get_preprocessed_subject_list.py --recon_suffix SS3T` to obtain a list of subjects that has been pre-processed and not yet reconstructed using SS3T

**4.3.2: Run SS3T ODF reconstruction**
<br>
Run `~/analysis/data_processing/PNC_qsirecon_ss3t.sh` 

**4.3.3: Get subject list for SS3Tautotrack reconstruction**
<br>
Run `~/analysis/data_processing/subject_lists/get_preprocessed_subject_list.py --recon_suffix SS3Tautotrack` to obtain a list of subjects that has been pre-processed and not yet reconstructed using SS3Tautotrack

**4.3.4: Run autotrack based on SS3T reconstruction:**
<br>
Run `~/analysis/data_processing/PNC_qsirecon_ss3t_autotrack.sh`

## 5: Warp reconstructed bundles to MNI space and mask

Repeat these steps for each of the three reconstruction methods by using `GQIautotrack` , `CSDautotrack` and `SS3Tautotrack` . Examples below for GQI.
<br>
### 5.1: Get subject list

Run `~/analysis/data_processing/subject_lists/get_preprocessed_subject_list.py --recon_suffix GQIautotrack` to create a subject list of all subjects that have been reconstructed but not yet warped and masked.

### 5.2: Warp bundles to MNI space and create binary mask

Run `~/analysis/data_processing/warp_bundles_to_mni_and_mask.sh GQIautotrack`

## 6: Create list of excluded subjects

After processing the data, a list of subjects that will not be included in the analysis is created.
<br>
To derive this list, run `~/analysis/data_processing/subject_lists/qc.py`
<br>
This list checks for subjects with acquisition variants, subjects that could not be pre-processed or reconstructed and subjects that failed QC based on Roalf et al., 2016.

# Bundle Reliability Analysis

## 7: Reconstruction Fractions

### 7.1: Determine fractions of reconstructed bundles
Repeat this step for each of the three reconstruction methods `GQIautotrack` , `CSDautotrack` and `SS3Tautotrack` .
<br>
Run `~/analysis/fractions_reconstructed_bundles/get_reconstructed_bundles.py` for each of the three reconstruction methods. The reconstruction method is passed as the argument `recon_suffix` .
<br>
Example for GQI: `python3 get_reconstructed_bundles.py --recon_suffix GQIautotrack` .

### 7.2: Plot the fractions 🎨
Run `~/analysis/fractions_reconstructed_bundles/plot_recon_fractions.ipynb` to create the plot of reconstruction fractions.

## 8: Dice Scores

### 8.1: Calculate dice scores
Repeat this step for each of the three reconstruction methods `GQIautotrack` , `CSDautotrack` and `SS3Tautotrack`.
<br>
Run `~/analysis/dice_scores/calculate_dice_scores.sh` for each of the three reconstruction methods by passing the recon_suffix as argument. Example for GQI: `sbatch calculate_dice_scores.sh GQIautotrack`

### 8.2: Plot full distributions 🎨
Run `~/analysis/dice_scores/plot_full_dice_distributions.py` to plot the full distributions of dice scores for each reconstruction method. The reconstruction method needs to be set at the top of the script as `GQI` , `CSD`  or `SS3T` .

### 8.3: Plot median distributions 🎨
Run `~/analysis/dice_scores/plot_median_dice_scores.ipynb` to plot the median (median within and between dice score per bundle) distributions for all reconstruction methods.

## 9: Discriminability

### 9.1: Calculate discriminability
Run `~/analysis/discriminability/discrim_two_sample_filtered.sh` for each combination of reconstruction methods to calculate the two sample discriminability.
<br>
Example for `GQI` and `CSD` : `sbatch discrim_two_sample_filtered.sh GQIautotrack CSDautotrack SS3Tautotrack` . This will calculate the the discriminability for GQI and CSD and determine whether there is a significant difference between the two. SS3T is passed as a third argument to perform the filtering and only include scans for which a given bundle was reconstructed for all three methods.

### 9.2: Plot discriminability 🎨
Run `~/analysis/discriminability/plot_discrim_two_sample.ipynb` to create the plot comparing discriminability between reconstruction methods for all reconstructed WM bundles.

## 10: Bundle Completeness

### 10.1: Calculate population maps
Repeat this step for all three reconstruction methods `GQIautotrack` , `CSDautotrack` and `SS3Tautotrack` .
<br>
Run `~/analysis/overlay_maps/calculate_overlay_maps.sh` to calculate sensitivity and specificity of each WM bundle for a given reconstruction method.
Example for GQI: `sbatch sensitivity_specificity.sh GQIautotrack`

### 10.2: Plot population maps over atlas bundles 🎨
This script requires it’s own python environment!
<br>
- Activate environment in terminal: `micromamba activate myavi`
- Start interactive python session in terminal with `ipython --gui=qt5`
- Run code from `~/analysis/overlay_maps/plot_population_map_on_atlas.py` in interactive python session to create the plots.

### 10.3: Extract atlas bundles from DSIStudio
- Download high-resolution HCP1065 1mm fib file from https://brain.labsolver.org/hcp_template.html and open it in DSIStudio. In the project directory this file can be found here: `~/data/HCP1065.1mm.fib.gz`
- Right-click DSIStudio installation and select `Show Package Contents` .
- Then open `/Applications/dsi_studio.app/Contents/MacOS/atlas/human/human.tt.gz` in DSIStudio on top of the HCP fib file.
- Now merge all WM bundles that have two underscores in the name to their parent bundle. E.g. `ProjectionBrainstem_CorticopontineTractR_Frontal` + `ProjectionBrainstem_CorticopontineTractR_Parietal` + `ProjectionBrainstem_CorticopontineTractR_Occipital` → `ProjectionBrainstem_CorticopontineTractR`
- Then select all bundles except for the Cerebellum and Cranial Nerves, right-click one of them and select `save all tracts as multiple files`
- These files should then be moved to `~/data/atlas_bundles/.`

### 10.4: Mask atlas bundles and warp to MNIc space
- Get T1w images from MNIb and MNIc space from template flow using datalad. These should be saved here:
    - `~/data/templateflow/tpl-MNI152NLin2009bAsym/tpl-MNI152NLin2009bAsym_res-1_T1w.nii.gz`
    - `~/data/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz`
- Calculate transform using the two T1w images by running `~/analysis/overlap/calculate_transform_mnib2c.sh`
- Mask and transform all atlas bundles by running `~/analysis/overlap/mask_and_warp_atlas_bundles.sh`

### 10.5: Calculate sensitivity and specificity of reconstructed bundles with atlas bundles
Repeat this step for all three reconstruction methods `GQIautotrack` , `CSDautotrack` and `SS3Tautotrack` .
<br>
Run `~/analysis/overlap/sensitivity_specificity.sh` to calculate sensitivity and specificity of each WM bundle for a given reconstruction method.
Example for GQI: `sbatch sensitivity_specificity.sh GQIautotrack`

### 10.6: Plot sensitivity and specificity 🎨
Run `~/analysis/overlap/plot_sensitivity_specificity.ipynb` to create the plots of sensitivity and specificity.

# Prediction Analysis

## 11: Prepare Data

### 11.1: Prepare feature csvs

**11.1.1:** Run `~/analysis/prediction/prep_prediction_files/move_bundle_stats.sh` for all three reconstructions.
Example for GQI: `bash move_bundle_stats.sh GQIautotrack`
<br>
**11.1.2:** Run `~/analysis/prediction/prep_prediction_files/create_feature_csvs.py` to create the feature csv’s.
<br>
**11.1.3:** Plot feature ICCs by running `~/analysis/prediction/plot_feature_icc.ipynb` 🎨
<br>
This has to be run for the three different features considered here, i.e., `total_volume_mm3` , `dti_fa` , `md` . The current feature for which the plot is created can be adjusted at the beginning of the manuscript.

### 11.2: Prepare confound csv
Run `~/analysis/prediction/prep_prediction_files/prepare_confounds_csv.py` to extract the head movement for all scans and create one confound csv containing all confounds of interest for all subjects.

## 12: Run Prediction

Prediction was run on a different system, so the features, confound and target files were moved there.

The prediction performed in the main analysis can be run by submitting `~/analysis/prediction/predict_cognition.submit` to the cluster.

- To perform the supplementary analysis including TBV as a confound replace all instances of `sex,ageAtScan1,mean_fd` with `sex,ageAtScan1,mean_fd,mprage_antsCT_vol_TBV` in the submit file.
- To perform the supplementary analysis for predicting two additional cognitive traits replace all instances of `cpxresAZv2` with either `exeAZv2` or `ciqAZv2` .

The results were copied to CUBIC and can be found at `/cbica/projects/clinical_dmri_benchmark/results/prediction/remove_confounds_features`

## 13: Compare Prediction Model Performances

Run `~/analysis/prediction/compare_model_performances.py` to obtain a csv with p-values that imply if there is a significant difference between two considered models.

## Step 14: Plot Prediction Results

### 14.1: Plot prediction accuracy 🎨
Run `~/analysis/prediction/plot_prediction_results.ipynb` to plot the prediction accuracy for the main analysis.

- To plot results for the supplementary analysis including TBV as a confound, set `TBV_AS_CONFOUND = True` at the beginning of the script.
- To plot results for the supplementary analysis for the two additional cognition targets set `TARGET = "exeAZv2"` or `TARGET = "ciqAZv2"` at the beginning of the script.

### 14.2: Plot prediction similarity 🎨
Run `~analysis/prediction/plot_prediction_reliability.ipynb` to plot the similarity between prediction from different scans for the main analysis.

- To plot results for the supplementary analysis including TBV as a confound, set `TBV_AS_CONFOUND = True` at the beginning of the script.
- To plot results for the supplementary analysis for the two additional cognition targets set `TARGET = "exeAZv2"` or `TARGET = "ciqAZv2"` at the beginning of the script.