#!/bin/sh
# 
#

#Initialization of parameters
data_path=/home/sbedard/Projects/Dermatomal_Mapping_R01/data/BIDS/derivatives

task=tens
copes=(cope1 cope2 cope3 cope4)
subjects=(sub-DMAim1HC004 sub-DMAim1HC006 sub-DMAim1HC007 sub-DMAim1HC015 sub-DMAim1HC018 sub-DMAim1HC020 sub-DMAim1HC030 sub-DMAim1HC033 sub-DMAim1HC001 sub-DMAim1HC005 sub-DMAim1HC016 sub-DMAim1HC017 sub-DMAim1HC022 sub-DMAim1HC023 sub-DMAim1HC027 sub-DMAim1HC025 sub-DMAim1HC035 sub-DMAim1HC008 sub-DMAim1HC031 sub-DMAim1HC032 sub-DMAim1HC034 sub-DMAim1HC019 sub-DMAim1HC037 sub-DMAim1HC028 sub-DMAim1HC038 sub-DMAim1HC039 sub-DMAim1HC009 sub-DMAim1HC045 sub-DMAim1HC002 sub-DMAim1HC047 sub-DMAim1HC029 sub-DMAim1HC036 sub-DMAim1HC046 sub-DMAim1HC042 sub-DMAim1HC003 sub-DMAim1HC053 sub-DMAim1HC052 sub-DMAim1HC051 sub-DMAim1HC054 sub-DMAim1HC013)

rm -f subject_metrics.txt
echo task cope subject zscore_sc voxels_sc lr_sc >> subject_metrics.txt

for cope in ${copes[@]}; do
    for subject in ${subjects[@]}; do

        session=""

        echo ${task} ${cope} ${subject}
        #sub-DMAim1HC020_ses-spinalcord_task-tens_run-average_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level
        zscore_sc=`fslstats ${data_path}/${subject}/ses-${session}spinalcord/func/${subject}_ses-${session}spinalcord_task-${task}_run-average_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/${cope}.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/mask_cord_N40.nii.gz -M`
        voxels_sc=`fslstats ${data_path}/${subject}/ses-${session}spinalcord/func/${subject}_ses-${session}spinalcord_task-${task}_run-average_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/${cope}.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/mask_cord_N40.nii.gz -V | cut -d " " -f1`
        left_voxels_sc=`fslstats ${data_path}/${subject}/ses-${session}spinalcord/func/${subject}_ses-${session}spinalcord_task-${task}_run-average_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/${cope}.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/rois_n40/left_sc_mask.nii.gz -V | cut -d " " -f1`
        right_voxels_sc=`fslstats ${data_path}/${subject}/ses-${session}spinalcord/func/${subject}_ses-${session}spinalcord_task-${task}_run-average_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/${cope}.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/rois_n40/right_sc_mask.nii.gz -V | cut -d " " -f1`

        if [ "${left_voxels_sc}" -gt 0 ] || [ "${right_voxels_sc}" -gt 0 ]; then
             lr_sc=`echo "scale=3; (${left_voxels_sc} - ${right_voxels_sc}) / (${left_voxels_sc} + ${right_voxels_sc})" | bc -l`
        else
             lr_sc=0
        fi

        echo ${task} ${cope} ${subject} ${zscore_sc} ${voxels_sc} ${lr_sc} >> subject_metrics.txt

    done
done
