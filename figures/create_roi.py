#!/usr/bin/env python
# -*- coding: utf-8
# For usage, type: python create_roi.py -h

# To create ROIS for PAM50 space for ROI analysis, use the following command (after changing the paths):
#python create_roi.py -label ${SCT_DIR}/data/PAM50/ -mask ~/Projects/Dermatomal_Mapping_R01/data/BIDS/derivatives/masks/mask_cord_N40.nii.gz -levels 6 7 8 -thr 0.5 -o-folder ~/Projects/Dermatomal_Mapping_R01/data/BIDS/derivatives/masks/rois_n40/ 
# Author: Sandrine Bédard

import os
import argparse
import logging
import numpy as np
import nibabel as nib
import sys
from scipy.ndimage import center_of_mass
import subprocess


FNAME_LOG = 'roi_info.txt'

ROIS = [
    'PAM50_atlas_30.nii.gz',
    'PAM50_atlas_31.nii.gz',
    'PAM50_atlas_34.nii.gz',
    'PAM50_atlas_35.nii.gz'
]

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # default: logging.DEBUG, logging.INFO
hdlr = logging.StreamHandler(sys.stdout)
logging.root.addHandler(hdlr)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Create ROIS for functional analysis for right/left dorsal and ventral horns of the spinal cord.")
    parser.add_argument("-path-PAM50",
                        required=True,
                        type=str,
                        help="Folder with labels with atlas and spinal levels")
    parser.add_argument("-mask",
                        required=True,
                        type=str,
                        help="Mask of coverage to restrict the analysis")
    parser.add_argument("-levels",
                        nargs='+',
                        required=True,
                        default=[4, 5, 6, 7, 8, 9],
                        help="Spinal levels to use to create roi")
    parser.add_argument("-o-folder",
                        required=True,
                        help="Output folder to write ROIS")
    parser.add_argument("-crop",
                        required=False,
                        default=[32, 75, 34, 75, 691, 263],
                        nargs='+',
                        type=int,
                        help="Cropping parameters for the ROIs")
    return parser


def save_Nifti1(data, original_image, filename):
    empty_header = nib.Nifti1Header()
    image = nib.Nifti1Image(data, original_image.affine, empty_header)
    nib.save(image, filename)


def main():

    args = get_parser().parse_args()
    # Get input argments
    path_labels = args.path_PAM50
    path_atlas = os.path.join(path_labels, 'atlas')
    levels = args.levels
    # Initialize values for each label
    output_folder = args.o_folder
    # Create output folder if does not exist.
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    crop = args.crop
    # Load mask to restrict the analysis
    mask_nib = nib.load(args.mask)
    mask_np = mask_nib.get_fdata()
    mask_np_crop = np.zeros(mask_np.shape)
    # Dump log file there
    if os.path.exists(FNAME_LOG):
        os.remove(FNAME_LOG)
    fh = logging.FileHandler(os.path.join(output_folder, FNAME_LOG))
    logging.root.addHandler(fh)

    # Create right and left hemicord for entire cord
    os.chdir(output_folder)
    # Crop the mask to keep only the area of interest
    file_cord=os.path.join(path_labels, 'template', 'PAM50_cord.nii.gz')
    subprocess.run([
        'fslroi',
        file_cord,
        'PAM50_cord_cropped.nii.gz',
        str(crop[0]), str(crop[1]),
        str(crop[2]), str(crop[3]),
        str(crop[4]), str(crop[5])
    ], check=True)
    # Apply mask on cord cropped
    subprocess.run(['fslmaths', 'PAM50_cord_cropped.nii.gz', '-mul', args.mask, 'PAM50_cord_cropped_group_mask.nii.gz'])
    # Create right and left hemicord
    subprocess.run([
        "sct_maths",
        "-i", os.path.join(path_atlas, "PAM50_atlas_00.nii.gz"),
        "-add", os.path.join(path_atlas, "PAM50_atlas_02.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_04.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_06.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_08.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_10.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_12.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_14.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_16.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_18.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_20.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_22.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_24.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_26.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_28.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_30.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_32.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_34.nii.gz"),
        "-o", "PAM50_atlas_left_hemi_cord.nii.gz"
    ])
    subprocess.run([
        "sct_maths",
        "-i", os.path.join(path_atlas, "PAM50_atlas_01.nii.gz"),
        "-add", os.path.join(path_atlas, "PAM50_atlas_03.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_05.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_07.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_09.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_11.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_13.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_15.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_17.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_19.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_21.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_23.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_25.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_27.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_29.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_31.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_33.nii.gz"),
        os.path.join(path_atlas, "PAM50_atlas_35.nii.gz"),
        "-o", "PAM50_atlas_right_hemi_cord.nii.gz"
    ])
    subprocess.run([
        "sct_maths",
        "-i", "PAM50_atlas_right_hemi_cord.nii.gz",
        "-bin", "0.5",
        "-o", "PAM50_atlas_right_hemi_cord_bin.nii.gz"
        ])

    subprocess.run([
        "sct_maths",
        "-i", "PAM50_atlas_left_hemi_cord.nii.gz",
        "-bin", "0.5",
        "-o", "PAM50_atlas_left_hemi_cord_bin.nii.gz"
    ])
    # Crop and apply mask:
    subprocess.run([
        'fslroi',
        "PAM50_atlas_left_hemi_cord_bin.nii.gz",
        'PAM50_atlas_left_hemi_cord_bin_crop.nii.gz',
        str(crop[0]), str(crop[1]),
        str(crop[2]), str(crop[3]),
        str(crop[4]), str(crop[5])
    ], check=True)
    subprocess.run([
        'fslroi',
        "PAM50_atlas_right_hemi_cord_bin.nii.gz",
        'PAM50_atlas_right_hemi_cord_bin_crop.nii.gz',
        str(crop[0]), str(crop[1]),
        str(crop[2]), str(crop[3]),
        str(crop[4]), str(crop[5])
    ], check=True)
    subprocess.run(['fslmaths', 'PAM50_atlas_right_hemi_cord_bin_crop.nii.gz', '-mul', args.mask, 'PAM50_atlas_right_hemi_cord_bin_crop_group_mask.nii.gz'])
    subprocess.run(['fslmaths', 'PAM50_atlas_left_hemi_cord_bin_crop.nii.gz', '-mul', args.mask, 'PAM50_atlas_left_hemi_cord_bin_crop_group_mask.nii.gz'])
    print(f"Created PAM50_atlas_left_hemi_cord_bin_crop_group_mask.nii.gz and PAM50_atlas_right_hemi_cord_bin_crop_group_mask.nii.gz")

    # Create GM mask cropped and with group mask
    subprocess.run([
        'fslroi',
        os.path.join(path_labels, 'template', 'PAM50_gm.nii.gz'),
        'PAM50_gm_crop.nii.gz',
        str(crop[0]), str(crop[1]),
        str(crop[2]), str(crop[3]),
        str(crop[4]), str(crop[5])
    ], check=True)
    subprocess.run(['fslmaths', 'PAM50_gm_crop.nii.gz', '-mul', args.mask, 'PAM50_gm_crop_group_mask.nii.gz'])
    # Binarize GM mask
    subprocess.run([
        "sct_maths",
        "-i", "PAM50_gm_crop_group_mask.nii.gz",
        "-bin", "0.5",
        "-o", "PAM50_gm_crop_group_mask.nii.gz"
    ])
    print(f"Created PAM50_gm_crop_group_mask.nii.gz")
    # Create right left GM
    subprocess.run([
        "sct_maths",
        "-i", "PAM50_gm_crop_group_mask.nii.gz",
        "-mul", "PAM50_atlas_right_hemi_cord_bin_crop_group_mask.nii.gz",
        "-o", "PAM50_gm_right_hemi_cord_group_mask.nii.gz"
    ])
    subprocess.run([
        "sct_maths",
        "-i", "PAM50_gm_crop_group_mask.nii.gz",
        "-mul", "PAM50_atlas_left_hemi_cord_bin_crop_group_mask.nii.gz",
        "-o", "PAM50_gm_left_hemi_cord_group_mask.nii.gz"
    ])
    print(f"Created PAM50_gm_right_hemi_cord_group_mask.nii.gz and PAM50_gm_left_hemi_cord_group_mask.nii.gz")

    i = 1
    # Loop through levels
    path_spinal_levels = os.path.join(path_labels, 'template', 'PAM50_spinal_levels.nii.gz')
    # Crop and apply mask on spinal levels
    subprocess.run([
        'fslroi',
        path_spinal_levels,
        'PAM50_spinal_levels_crop.nii.gz',
        str(crop[0]), str(crop[1]),
        str(crop[2]), str(crop[3]),
        str(crop[4]), str(crop[5])
    ], check=True)
    subprocess.run(['fslmaths', 'PAM50_spinal_levels_crop.nii.gz', '-mul', args.mask, 'PAM50_spinal_levels_crop_group_mask.nii.gz'])
    path_spinal_levels = 'PAM50_spinal_levels_crop_group_mask.nii.gz'
    # Apply spinal level mask to each roi
    subprocess.run(['fslmaths', 'PAM50_gm_right_hemi_cord_group_mask.nii.gz', '-mul', 'PAM50_spinal_levels_crop_group_mask.nii.gz', 'PAM50_gm_right_hemi_cord_levels.nii.gz'])
    subprocess.run(['fslmaths', 'PAM50_gm_left_hemi_cord_group_mask.nii.gz', '-mul', 'PAM50_spinal_levels_crop_group_mask.nii.gz', 'PAM50_gm_left_hemi_cord_levels.nii.gz'])
    # Save rois for each level
    for level in levels:
        print(f'Creating roi for level {level}')
        # Create mask for the level
        subprocess.run([
            'fslmaths',
            'PAM50_gm_left_hemi_cord_levels.nii.gz',
            '-thr', str(int(level) - 0.5),
            '-uthr', str(int(level) + 0.5),
            '-bin',
            f'C{level}_PAM50_gm_left_hemi_cord_group_mask.nii.gz.nii.gz'
        ], check=True)
        subprocess.run([
            'fslmaths',
            'PAM50_gm_right_hemi_cord_levels.nii.gz',
            '-thr', str(int(level) - 0.5),
            '-uthr', str(int(level) + 0.5),
            '-bin',
            f'C{level}_PAM50_gm_right_hemi_cord_group_mask.nii.gz.nii.gz'
        ], check=True)

    # rename the rois
    os.rename('C6_PAM50_gm_left_hemi_cord_group_mask.nii.gz.nii.gz', 'C6_left_sc_gm_mask.nii.gz')
    os.rename('C6_PAM50_gm_right_hemi_cord_group_mask.nii.gz.nii.gz', 'C6_right_sc_gm_mask.nii.gz')
    os.rename('C7_PAM50_gm_left_hemi_cord_group_mask.nii.gz.nii.gz', 'C7_left_sc_gm_mask.nii.gz')
    os.rename('C7_PAM50_gm_right_hemi_cord_group_mask.nii.gz.nii.gz', 'C7_right_sc_gm_mask.nii.gz')
    os.rename('C8_PAM50_gm_left_hemi_cord_group_mask.nii.gz.nii.gz', 'C8_left_sc_gm_mask.nii.gz')
    os.rename('C8_PAM50_gm_right_hemi_cord_group_mask.nii.gz.nii.gz', 'C8_right_sc_gm_mask.nii.gz')
    os.rename('PAM50_gm_left_hemi_cord_group_mask.nii.gz', 'left_sc_gm_mask.nii.gz')
    os.rename('PAM50_gm_right_hemi_cord_group_mask.nii.gz', 'right_sc_gm_mask.nii.gz')
    os.rename('PAM50_atlas_left_hemi_cord_bin_crop_group_mask.nii.gz', 'left_sc_mask.nii.gz')
    os.rename('PAM50_atlas_right_hemi_cord_bin_crop_group_mask.nii.gz', 'right_sc_mask.nii.gz')

if __name__ == "__main__":
    main()
