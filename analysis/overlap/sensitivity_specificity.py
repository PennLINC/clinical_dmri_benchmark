import os
import SimpleITK as sitk
import pandas as pd
import numpy as np
import sys

BUNDLE_MASK_ROOT = "/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs"
ATLAS_MASK_ROOT = "/cbica/projects/clinical_dmri_benchmark/data/atlas_bundles"
POPULATION_MAP_ROOT = "/cbica/projects/clinical_dmri_benchmark/results/overlay_maps"
OUTPUT_ROOT = "/cbica/projects/clinical_dmri_benchmark/results/overlap/"
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# Identify dataset from system argument
reconstruction = sys.argv[1]

# List of connections to compute overlap measures for
tract_names_file = "../../data/bundle_names.txt"
with open(tract_names_file, 'r') as f:
    tract_names = [line.strip() for line in f.readlines()]
# Function to compute sensitivity and specificity values for each subject-specific connection based on atlas connection overlap


def compute_sensitivity_specificity(sub_mask, template_mask, union):
    pred_np = sitk.GetArrayFromImage(sub_mask)[union]
    truth_np = template_mask[union]
    TP = np.sum((pred_np == 1) & (truth_np == 1))
    FP = np.sum((pred_np == 1) & (truth_np == 0))
    TN = np.sum((pred_np == 0) & (truth_np == 0))
    FN = np.sum((pred_np == 0) & (truth_np == 1))
    sensitivity = TP / (TP + FN) if (TP + FN) > 0 else np.nan
    specificity = TN / (TN + FP) if (TN + FP) > 0 else np.nan
    return sensitivity, specificity


# Output
overlap_results = []

# Identify all subject-specific tract masks in template space
subject_masks_path = f"{BUNDLE_MASK_ROOT}/qsirecon-{reconstruction}"
subids = os.listdir(subject_masks_path)
runs = ["run-01", "run-02"]

for tract_name in tract_names:
    print(tract_name)
    tract_name_short = tract_name.replace("_", "").replace("-", "")

    # Read probabilistic maps for all three methods
    prob_map_gqi = sitk.GetArrayFromImage(sitk.ReadImage(os.path.join(
        POPULATION_MAP_ROOT, "GQIautotrack", tract_name_short + ".nii.gz")))
    prob_map_csd = sitk.GetArrayFromImage(sitk.ReadImage(os.path.join(
        POPULATION_MAP_ROOT, "CSDautotrack", tract_name_short + ".nii.gz")))
    prob_map_ss3t = sitk.GetArrayFromImage(sitk.ReadImage(os.path.join(
        POPULATION_MAP_ROOT, "SS3Tautotrack", tract_name_short + ".nii.gz")))
    prob_map_gqi[prob_map_gqi > 0] = 1
    prob_map_csd[prob_map_csd > 0] = 1
    prob_map_ss3t[prob_map_ss3t > 0] = 1

    # Read in template (atlas) tract mask
    atlas_mask_path = f"{ATLAS_MASK_ROOT}/{tract_name}_MNIc.nii.gz"
    atlas_mask = sitk.GetArrayFromImage(
        sitk.ReadImage(atlas_mask_path, sitk.sitkUInt8))

    # calculate union between population maps and atlas tract to use as mask when calculating subject specific specificity
    # and sensitivity. Due to large amounts of background around the WM tracts, specificity would always be close to 1 without cropping to the union.
    union = np.logical_or.reduce(
        [prob_map_gqi != 0, prob_map_csd != 0, prob_map_ss3t != 0, atlas_mask != 0])
    
    for subid in subids:
        for run in runs:
            mask_name = subid + "_ses-PNC1_" + run + \
                "_space-MNI152NLin2009cAsym_bundle-" + tract_name_short + "_mask.nii.gz"
            mask_path = os.path.join(
                subject_masks_path, subid, "ses-PNC1", "dwi", "MNI", mask_name)
            if os.path.exists(mask_path):
                mask = sitk.ReadImage(mask_path, sitk.sitkUInt8)
                sensitivity, specificity = compute_sensitivity_specificity(
                    mask, atlas_mask, union)
                overlap_results.append({
                    "subject_id": subid,
                    "bundle": tract_name,
                    "run": run,
                    "sensitivity": sensitivity,
                    "specificity": specificity
                })

overlap_results_df = pd.DataFrame(overlap_results)
overlap_results_df.to_csv(
    OUTPUT_ROOT + reconstruction + "_overlap.csv", index=False)
