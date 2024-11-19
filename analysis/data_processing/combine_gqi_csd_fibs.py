from scipy.io import loadmat, savemat
import os
import numpy as np
import argparse


def combine_gqi_and_csd_fib_files(path_gqi_file: str, path_csd_file: str):
    """
    Combine the GQI and CSD .fib-files such that the new CSD fib file contains ODF information
    from the old CSD file and DTI maps from the GQI file.

    Args:
      path_gqi_file: Full path to the GQI file
      path_csd_file: Full path to the csd file. This will be overwritten with the updated csd file.
    """

    gqi_file = loadmat(path_gqi_file, appendmat=False)
    keys_gqi = [key for key in gqi_file]

    csd_file = loadmat(path_csd_file, appendmat=False)
    keys_csd = [key for key in csd_file]

    new_csd_file = gqi_file.copy()
    for i in range(3):
        new_csd_file["fa" + str(i)] = csd_file["fa" + str(i)]
        new_csd_file["index" + str(i)] = csd_file["index" + str(i)]

    for gqi_key in keys_gqi:
        if gqi_key.startswith("odf"):
            del new_csd_file[gqi_key]
    for csd_key in keys_csd:
        if csd_key.startswith("odf"):
            new_csd_file[csd_key] = csd_file[csd_key]

    savemat(path_csd_file, new_csd_file, format="4", appendmat=False)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gqi_path",
        type=str,
        required=True,
        help="Path of the GQI .fib-file",
    )
    parser.add_argument(
        "--csd_path",
        type=str,
        required=True,
        help="Path of the csd .fib-file",
    )
    args = parser.parse_args()
    GQI_PATH = args.gqi_path
    CSD_PATH = args.csd_path

    combine_gqi_and_csd_fib_files(GQI_PATH, CSD_PATH)
