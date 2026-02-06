#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Creates an avreage tSNR map from native space and an include list
# Example command:  python average_tsnr_map.py -path-in ~/Projects/Dermatomal_Mapping_R01/data/BIDS/derivatives/ -include ~/codes/Dermatomal_Mapping_R01/include_n35.yml -o ~/dermatomal_mapping_proprocessing_2025-04-11_ventral_dorsal_runALL/results/tsnr_maps_n35/

import matplotlib.pyplot as plt
import pandas as pd
import argparse
import yaml
import numpy as np
import logging
import sys
import os
import glob
import nibabel as nib
FNAME_LOG = 'log_stats.txt'

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # default: logging.DEBUG, logging.INFO
hdlr = logging.StreamHandler(sys.stdout)
logging.root.addHandler(hdlr)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Computes avreage tSNR map in PAM50 template space from native space tSNR maps.",)
    parser.add_argument('-path-in', required=True, type=str,
                        help="Path data_processed where the tSNR maps are stored.")
    parser.add_argument('-include', required=False, type=str,
                        default='include.yml',
                        help="Inlcude list .yml file with subjects to include. If not provided, all subjects found will be included.")
    parser.add_argument('-o', required=False, type=str,
                        help="Path output to put tsnr maps in PAM50 template space.")

    return parser


def main():

    args = get_parser().parse_args()
    # Get input arguments
    input_folder = os.path.abspath(args.path_in)
    include_file = os.path.abspath(args.include)
    output_folder = os.path.abspath(args.o)
    # Create output folder if does not exist.
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    os.chdir(output_folder)

    # Dump log file there
    if os.path.exists(FNAME_LOG):
        os.remove(FNAME_LOG)
    fh = logging.FileHandler(os.path.join(FNAME_LOG))
    logging.root.addHandler(fh)
    # Create a list with subjects to exclude if input .yml config file is passed
    if args.include is not None:
        # Check if input yml file exists
        if os.path.isfile(args.include):
            fname_yml = args.include
        else:
            sys.exit("ERROR: Input yml file {} does not exist or path is wrong.".format(args.include))
        with open(fname_yml, 'r') as stream:
            try:
                include = list(yaml.safe_load(stream))
            except yaml.YAMLError as exc:
                logger.error(exc)
    else:
        include = []
    logger.info(include)

    # Find tSNR maps
    #tsnr_maps = glob.glob(os.path.join(input_folder, '*/*/*/*/*mc2_tsnr.nii.gz'))
   # logger.info("Found tSNR maps: {}".format(tsnr_maps))
    # Remove subjects not in include list
    if include:
        list_tsnr_maps = []
        for sub in include:
            tsnr_maps = glob.glob(os.path.join(input_folder, sub, 'ses-spinalcord', 'func', 'run-*', '*mc2_tsnr.nii.gz'))
            logger.info("Found tSNR maps for {}: {}".format(sub, tsnr_maps))
            # Warp tSNR maps to PAM50 template space
            for tsnr_map in tsnr_maps:
                run = tsnr_map.split('_')[-4].split('-')[-1]  # Extract run number from filename
                logger.info("Processing subject: {}, run: {}".format(sub, run))
                # Example: sub-DMAim1HC005_ses-spinalcord_task-tens
                 # warp_sub-DMAim1HC005_ses-spinalcord_task-tens_run-1_bold_mc2_mean2PAM50_t2.nii.gz
                logger.info("Warping tSNR map {} to PAM50 template space.".format(tsnr_map))
                path_PAM50 = os.path.join('$SCT_DIR/data/PAM50/template/', 'PAM50_t2.nii.gz')
                path_warp = os.path.join(os.path.dirname(tsnr_map), f'warp_{sub}_ses-spinalcord_task-tens_run-{run}_bold_mc2_mean2PAM50_t2.nii.gz')
                filename_o = os.path.join(output_folder, os.path.basename(tsnr_map))
                # Check if output file exists, if so, skip command
                if os.path.exists(filename_o):
                    logger.info("Output file {} already exists. Skipping command.".format(filename_o))
                else:
                # Construct command to warp tSNR map to PAM50 template space
                    command = f'sct_apply_transfo -i {tsnr_map} -d {path_PAM50}  -w {path_warp} -x linear -o {filename_o}'
                    logger.info("Running command: {}".format(command))
                    os.system(command)
                list_tsnr_maps.extend([filename_o])

                #warp_sub-DMAim1HC005_ses-spinalcord_task-tens_run-1_bold_mc2_mean2PAM50_t2
        file_nib = nib.load(list_tsnr_maps[0])
        file_data = np.array(file_nib.get_fdata())
        sum_data = np.zeros(shape=file_data.shape)
        for tsnr_map in list_tsnr_maps:
            file_nib = nib.load(tsnr_map)
            sum_data +=np.array(file_nib.get_fdata())
            logger.info(tsnr_map)
        # Compute mean tSNR map for each run (1 to 3)
        for run_num in range(1, 4):
            run_maps = [tsnr_map for tsnr_map in list_tsnr_maps if f'run-{run_num}_' in os.path.basename(tsnr_map)]
            if run_maps:
                sum_run = np.zeros(shape=file_data.shape)
                for tsnr_map in run_maps:
                    file_nib_run = nib.load(tsnr_map)
                    sum_run += np.array(file_nib_run.get_fdata())
                mean_run = sum_run / len(run_maps)
                nii_mean_run = nib.Nifti1Image(mean_run, file_nib.affine)
                fname_out_run = f'mean_tsnr_PAM50_run-{run_num}.nii.gz'
                print('saving ...', os.path.join(output_folder, fname_out_run))
                nib.save(nii_mean_run, os.path.join(output_folder, fname_out_run))
        mean_data = sum_data / len(list_tsnr_maps)
        nii_mean= nib.Nifti1Image(mean_data, file_nib.affine)
        fname_out_levels = 'mean_tsnr_PAM50' + '.nii.gz'
        print('saving ...', os.path.join(output_folder, fname_out_levels))
        nib.save(nii_mean, os.path.join(output_folder, fname_out_levels))
if __name__ == "__main__":
    main()
