#!/usr/bin/env python
import argparse
import os
import pandas as pd
import shutil
import gzip
import nibabel as nb
import numpy as np
import glob

def stat_txt_to_df(stat_txt_file: str, bundle_name: str):
    """ Converts the DSIStudio stats txt file to a line of a dataframe.
    If no bundle stats file could be found. Only the bundle name will be indicated
    in the row of the dataframe
    --- Adapted from qsirecon v 0.23.2 ---

    Args:
        stat_txt_file: path to the stats txt file created by DSIStudio, "NA" if the file doesn't exist
        bundle_name: Name of the corresponding bundle to be shown in the dataframe
    """
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
    """ This function converts the trk bundle files that are output from 
    DSIStudio to tck files and saves the converted file with the same
    name the original file had.
    --- Adapted from qsirecon v 0.23.2 ---

    Args:
        preprocessed_dwi: link to the pre-processed dwi image
        trk_file: link to the trk file
    """
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
    """
    Loop over all bundles for a given subject and convert the outputs from the DSIStudio format to 
    the qsiprep format. This includes moving the files out of separate folders, renaming them 
    and combining separate stat files into one larger stats file.
    --- Adapted from qsirecon v 0.23.2 ---

    Args:
        path_atk_outputs: root directory of the DSIStudio autotrack output for this subject
        bundles: list of expected bundles (bundles that were tried to track)
        subid: ID of the considered subjects
        path_qsiprep_data: path to the preprocessed data of this subject (necessary to convert the trk to tck file)

    """
    for run in ["run-01", "run-02"]:
        stats_rows = []
        found_bundle_files = []
        found_bundle_names = []
        for bundle in bundles:
            bundle_path = glob.glob(f"{path_atk_outputs}/{bundle}/{subid}_ses-PNC1*_{run}_space-T1w_dwimap.{bundle}.trk.gz")
            if bundle_path:
                bundle_path = bundle_path[0]
                bundle_file_name_prefix = os.path.basename(bundle_path).split('_space-T1w_')[0] + '_space-T1w'
                stat_file_name = os.path.join(path_atk_outputs, bundle, bundle_file_name_prefix + "_dwimap." + bundle + ".stat.txt")
                if os.path.exists(stat_file_name) == True:
                    stats_rows.append(stat_txt_to_df(stat_file_name, bundle))
                else:
                    stats_rows.append(stat_txt_to_df("NA", bundle))
                if os.path.exists(bundle_path):
                    found_bundle_files.append(bundle_path)
                    found_bundle_names.append(bundle)
            else:
                stats_rows.append(stat_txt_to_df("NA", bundle))
                continue
        stats_df = pd.DataFrame(stats_rows)
        stats_df.to_csv(os.path.join(path_atk_outputs, bundle_file_name_prefix + "_bundlestats.csv"), index=False)
        for bundle_file, bundle_name in zip(found_bundle_files, found_bundle_names):
            new_bundle_file = os.path.join(path_atk_outputs, bundle_file_name_prefix + "_bundle-" + bundle_name.replace("_", "").replace("-", "") + "_streamlines.trk.gz")
            shutil.move(bundle_file, new_bundle_file)
            preprocessed_dwi = os.path.join(path_qsiprep_data, bundle_file_name_prefix + "_desc-preproc_dwi.nii.gz")
            convert_trk_to_tck(preprocessed_dwi, new_bundle_file)
            new_bundle_file_tck = os.path.join(path_atk_outputs, bundle_file_name_prefix + "_bundle-" + bundle_name.replace("_", "").replace("-", "") + "_streamlines.tck")
            os.system("gzip " + new_bundle_file_tck)
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
