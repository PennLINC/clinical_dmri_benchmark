#!/usr/bin/env python
import argparse
import os
import pandas as pd
import shutil
import gzip
import nibabel as nb
import numpy as np

def stat_txt_to_df(stat_txt_file: str, bundle_name: str):
    bundle_stats = {"bundle_name": bundle_name}
    if stat_txt_file == "NA":
        return bundle_stats
    with open(stat_txt_file, "r") as statf:
        lines = [
            line.strip().replace(" ", "_").replace("^", "").replace("(", "_").replace(")", "")
            for line in statf
        ]

    for line in lines:
        name, value = line.split("\t")
        bundle_stats[name] = float(value)

    return bundle_stats

def convert_trk_to_tck(preprocessed_dwi: str, trk_file: str):
    if trk_file.endswith(".gz"):
        with gzip.open(trk_file, "r") as trkf:
            dsi_trk = nb.streamlines.load(trkf)
    else:
        dsi_trk = nb.streamlines.load(trk_file)

    # load preprocessed dwi image
    dwi_img = nb.load(preprocessed_dwi)

    # convert to voxel coordinates
    pts = dsi_trk.streamlines._data
    zooms = np.abs(np.diag(dsi_trk.header["voxel_to_rasmm"])[:3])
    voxel_coords = pts / zooms
    voxel_coords[:, 0] = dwi_img.shape[0] - voxel_coords[:, 0]
    voxel_coords[:, 1] = dwi_img.shape[1] - voxel_coords[:, 1]

    # create new tck
    new_data = nb.affines.apply_affine(dwi_img.affine, voxel_coords)
    dsi_trk.tractogram.streamlines._data = new_data
    tck = nb.streamlines.TckFile(dsi_trk.tractogram)
    if trk_file.endswith('.gz'):
        tck_file = trk_file.strip('.gz')
        tck_file = tck_file.strip('.trk') + '.tck'
    else:
        tck_file = trk_file.strip('.trk') + '.tck'
    
    tck.save(tck_file)
    return

def aggregate_atk_results(path_atk_outputs: str, bundles: list, subid: str, path_qsiprep_data: str):    
    for run in ["run-01", "run-02"]:
        stats_rows = []
        found_bundle_files = []
        found_bundle_names = []
        for bundle in bundles:
            bundle_file_name = os.path.join(path_atk_outputs, bundle, subid + "_ses-PNC1_" + run + "_space-T1w_dwimap." + bundle + ".trk.gz")
            stat_file_name = os.path.join(path_atk_outputs, bundle, subid + "_ses-PNC1_" + run + "_space-T1w_dwimap." + bundle + ".stat.txt")
            if os.path.exists(stat_file_name) == True:
                stats_rows.append(stat_txt_to_df(stat_file_name, bundle))
            else:
                stats_rows.append(stat_txt_to_df("NA", bundle))
            if os.path.exists(bundle_file_name):
                found_bundle_files.append(bundle_file_name)
                found_bundle_names.append(bundle)
        stats_df = pd.DataFrame(stats_rows)
        stats_df.to_csv(os.path.join(path_atk_outputs, subid + "_ses-PNC1_" + run + "_space-T1w_bundlestats.csv"), index=False)
        for bundle_file, bundle_name in zip(found_bundle_files, found_bundle_names):
            new_bundle_file = os.path.join(path_atk_outputs, subid + "_ses-PNC1_" + run + "_space-T1w_bundle-" + bundle_name.replace("_", "") + "_streamlines.trk.gz")
            shutil.move(bundle_file, new_bundle_file)
            preprocessed_dwi = os.path.join(path_qsiprep_data, subid + "_ses-PNC1_" + run + "_space-T1w_desc-preproc_dwi.nii.gz")
            convert_trk_to_tck(preprocessed_dwi, new_bundle_file)
            os.remove(new_bundle_file)
    for bundle in bundles:
        bundle_folder = os.path.join(path_atk_outputs, bundle)
        if os.path.exists(bundle_folder):
            shutil.rmtree(bundle_folder)

    return

if __name__ == '__main__':
    BUNDLE_NAMES = "/cbica/projects/clinical_dmri_benchmark/clinical_dmri_benchmark/data/bundle_names.txt"

    with open(BUNDLE_NAMES, 'r') as f:
        bundles = f.read().splitlines()

    # Set up argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("path_atk_outputs", type=str, help="Path with all atk outputs for one subjects")
    parser.add_argument("subid", type=str, help="ID of the subject currently being processed")
    parser.add_argument("path_qsiprep_data", type=str, help="Root of the preprocessed data for one subject")
    args = parser.parse_args()

    aggregate_atk_results(args.path_atk_outputs, bundles, args.subid, args.path_qsiprep_data)
