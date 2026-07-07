#!/bin/sh
# 
#

#Initialization of parameters
data_path=/home/sbedard/nilab/Dnilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/preprocessing_ALL

task=tens
runs=(rightthumb leftthumb rightmiddle leftmiddle rightpinky leftpinky)
subjects=(sub-DMAim2HC001 sub-DMAim2HC002 sub-DMAim2HC003 sub-DMAim2HC004 sub-DMAim2HC013 sub-DMAim2HC009 sub-DMAim2HC012 sub-DMAim2HC020 sub-DMAim2HC011 sub-DMAim2HC005 sub-DMAim2HC016 sub-DMAim2HC021 sub-DMAim2HC018 sub-DMAim2HC023 sub-DMAim2HC014 sub-DMAim2HC025 sub-DMAim2HC017 sub-DMAim2HC019 sub-DMAim2HC027 sub-DMAim2HC026 sub-DMAim2HC006)

rm -f subject_metrics.txt
echo task run subject zscore_sc voxels_sc lr_sc >> subject_metrics.txt

for run in ${runs[@]}; do
    for subject in ${subjects[@]}; do

        session=""

        echo ${task} ${run} ${subject}
        #sub-DMAim2HC001_ses-spinalcord_task-tens_run-leftmiddle_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat
        zscore_sc=`fslstats ${data_path}/preprocessing_ALL/${subject}/ses-${session}spinalcord/func/run-${run}/${subject}_ses-${session}spinalcord_task-${task}_run-${run}_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/cope1.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/mask_n25.nii.gz -M`
        voxels_sc=`fslstats ${data_path}/preprocessing_ALL/${subject}/ses-${session}spinalcord/func/run-${run}/${subject}_ses-${session}spinalcord_task-${task}_run-${run}_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/cope1.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/mask_n25.nii.gz -V | cut -d " " -f1`
        left_voxels_sc=`fslstats ${data_path}/preprocessing_ALL/${subject}/ses-${session}spinalcord/func/run-${run}/${subject}_ses-${session}spinalcord_task-${task}_run-${run}_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/cope1.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/rois_n25/left_sc_mask.nii.gz -V | cut -d " " -f1`
        right_voxels_sc=`fslstats ${data_path}/preprocessing_ALL/${subject}/ses-${session}spinalcord/func/run-${run}/${subject}_ses-${session}spinalcord_task-${task}_run-${run}_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/cope1.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/rois_n25/right_sc_mask.nii.gz -V | cut -d " " -f1`

        if [ "${left_voxels_sc}" -gt 0 ] || [ "${right_voxels_sc}" -gt 0 ]; then
             lr_sc=`echo "scale=3; (${left_voxels_sc} - ${right_voxels_sc}) / (${left_voxels_sc} + ${right_voxels_sc})" | bc -l`
        else
             lr_sc=0
        fi

        echo ${task} ${run} ${subject} ${zscore_sc} ${voxels_sc} ${lr_sc} >> subject_metrics.txt

    done
done
