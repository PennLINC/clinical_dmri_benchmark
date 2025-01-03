import SimpleITK as sitk
import os
import argparse
import glob
import numpy as np

def get_statitistical_overlay_maps(
    root_qsirecon: str, root_output: str,
    excluded_subject_list: str, bundle: str
):
    bundle = bundle.replace("_", "").replace("-", "")
    subjects = [
        folder
        for folder in os.listdir(root_qsirecon)
        if os.path.isdir(os.path.join(root_qsirecon, folder))
        and folder.startswith("sub")
    ]
    with open(excluded_subject_list, 'r') as f:
        excluded_subjects = f.read().splitlines()
    for subject in excluded_subjects:
        if subject in subjects:
            subjects.remove(subject)

    if os.path.exists(os.path.join(root_output, bundle + ".nii.gz")):
        print("An overlay map already exists for bundle " + bundle + ". Skipping.")
        return
    counter = 0
    for subject in subjects:
        for run in ["run-01", "run-02"]:
            mask_path = os.path.join(
                root_qsirecon,
                subject,
                "ses-PNC1",
                "dwi",
                "MNI",
                f"{subject}_ses-PNC1_*{run}_space-MNI152NLin2009cAsym_bundle-{bundle}_mask.nii.gz",
            )
            matching_files = glob.glob(mask_path)
            if matching_files:
                bundle_image = sitk.ReadImage(matching_files[0])
                bundle_array = sitk.GetArrayFromImage(bundle_image)
                if counter == 0:
                    stats_overlap = bundle_array.astype(np.int64)
                    counter += 1
                else:
                    stats_overlap = stats_overlap + bundle_array
                    counter += 1
            else:
                continue
    stats_overlap = stats_overlap / counter
    print(stats_overlap.max())
    stats_overlap_img = sitk.GetImageFromArray(stats_overlap)
    stats_overlap_img.SetDirection(bundle_image.GetDirection())
    stats_overlap_img.SetOrigin(bundle_image.GetOrigin())
    stats_overlap_img.SetSpacing(bundle_image.GetSpacing())
    sitk.WriteImage(stats_overlap_img, os.path.join(root_output, bundle + ".nii.gz"))
    return


if __name__ == "__main__":
    # Setup argument parser
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
        help="Name of the considered bundle (e.g., CorpusCallosum)",
    )
    args = parser.parse_args()

    QSIRECON_SUFFIX = args.recon_suffix
    qsirecon_suffix_options = ["GQIautotrack", "SS3Tautotrack", "CSDautotrack"]
    assert (
        QSIRECON_SUFFIX in qsirecon_suffix_options
    ), f"Error: {QSIRECON_SUFFIX} is not a valid option."

    BUNDLE = args.bundle
    BUNDLE_ROOT = (
        "/cbica/projects/clinical_dmri_benchmark/results/qsirecon_outputs/qsirecon-"
        + QSIRECON_SUFFIX
    )
    OUTPUT_ROOT = (
        "/cbica/projects/clinical_dmri_benchmark/results/overlay_maps/"
        + QSIRECON_SUFFIX
    )
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    EXCLUDED_SBJ_LIST = "/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/analysis/data_processing/subject_lists/excluded_subjects.txt"

    get_statitistical_overlay_maps(BUNDLE_ROOT, OUTPUT_ROOT, EXCLUDED_SBJ_LIST, BUNDLE)
