#!/bin/sh
# 
#

#Initialization of parameters
data_path=/home/sbedard/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/
data_out=${data_path}/preprocessing_ALL/results/n36

task=tens
runs=(rightthumb leftthumb rightmiddle leftmiddle rightpinky leftpinky)
subjects=(sub-DMAim2HC001 sub-DMAim2HC002 sub-DMAim2HC003 sub-DMAim2HC004 sub-DMAim2HC013 sub-DMAim2HC009 sub-DMAim2HC012 sub-DMAim2HC020 sub-DMAim2HC011 sub-DMAim2HC005 sub-DMAim2HC016 sub-DMAim2HC021 sub-DMAim2HC018 sub-DMAim2HC023 sub-DMAim2HC014 sub-DMAim2HC025 sub-DMAim2HC017 sub-DMAim2HC019 sub-DMAim2HC027 sub-DMAim2HC026 sub-DMAim2HC006 sub-DMAim2HC041 sub-DMAim2HC044 sub-DMAim2HC038 sub-DMAim2HC029 sub-DMAim2HC030 sub-DMAim2HC034 sub-DMAim2HC057 sub-DMAim2HC039 sub-DMAim2HC054 sub-DMAim2HC042 sub-DMAim2HC046 sub-DMAim2HC046 sub-DMAim2HC032 sub-DMAim2HC043 sub-DMAim2HC056 sub-DMAim2HC040)
rois=(left_sc_gm_mask right_sc_gm_mask left_sc_mask right_sc_mask C6_left_sc_gm_mask C6_right_sc_gm_mask C7_left_sc_gm_mask C7_right_sc_gm_mask C8_left_sc_gm_mask C8_right_sc_gm_mask) # left_sc_vh_mask right_sc_vh_mask left_sc_vq_mask right_sc_vq_mask)
#rois=(left_sc_mask right_sc_mask left_vh_mask right_vh_mask left_vq_mask right_vq_mask)

mkdir -p ${data_out}
#rm -f subject_metrics_rois.txt
#echo task cope subject roi zscore >> subject_metrics_rois.txt
rm -f subject_metrics_rois.txt
echo task run subject region zscore_sc voxels_sc >> subject_metrics_rois.txt

for run in ${runs[@]}; do
    for subject in ${subjects[@]}; do
        for roi in ${rois[@]}; do

            session=""

            echo ${task} ${cope} ${subject} ${roi}

            zscore=`fslstats ${data_path}/preprocessing_ALL/${subject}/ses-${session}spinalcord/func/run-${run}/${subject}_ses-${session}spinalcord_task-${task}_run-${run}_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/cope1.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/rois_n25/${roi}.nii.gz -M`
            voxels=`fslstats ${data_path}/preprocessing_ALL/${subject}/ses-${session}spinalcord/func/run-${run}/${subject}_ses-${session}spinalcord_task-${task}_run-${run}_bold_mc2_pnm_stc2template_smooth225_trialwise_second_level.gfeat/cope1.feat/thresh_zstat1.nii.gz -k ${data_path}/masks/rois_n25/${roi}.nii.gz -V | cut -d " " -f1`

            echo ${task} ${run} ${subject} ${roi} ${zscore} ${voxels}
            echo ${task} ${run} ${subject} ${roi} ${zscore} ${voxels} >> subject_metrics_rois.txt

        done
    done
done

mv subject_metrics_rois.txt ${data_out}/subject_metrics_rois.txt