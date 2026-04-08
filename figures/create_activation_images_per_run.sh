#!/bin/sh
# 
#

#Initialization of parameters
data_path=/home/sbedard/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/group_level/
output_path=/home/sbedard/nilab/Dermatomal_Mapping_R01/Aim2/manuscripts/figures_screenshots/
spinal_cord_slices=(98 108 113 123 133 143)
spinal_cord_slices=(40 50 60 70 80 90 100 110 120 130 140 150 160 170 180 190)
task=tens
#copes=(amp_1 amp_2 amp_3 amp_4 linear)
copes=(cope1)
type=FE3.1
min=5
max=9
n=10
runs=(rightthumb rightmiddle rightpinky leftthumb leftmiddle leftpinky)
mkdir -p "${output_path}n${n}_${type}"
for run in ${runs[@]}; do
	for cope in ${copes[@]}; do

		echo ${run} ${cope}
		# Crop PAM50 T2s and T2w
		fslroi ${SCT_DIR}/data/PAM50/template/PAM50_t2.nii.gz PAM50_t2_crop.nii.gz 32 75 34 75 691 263
		fslroi ${SCT_DIR}/data/PAM50/template/PAM50_t2s.nii.gz PAM50_t2s_crop.nii.gz 32 75 34 75 691 263

		overlay 0 1 PAM50_t2s_crop.nii.gz 300 800 ${data_path}/group_level_n${n}_${run}_${type}.gfeat/${cope}.feat/stats/zstat1.nii.gz $min $max ${cope}_overlay
		overlay 0 1 PAM50_t2_crop.nii.gz 0 3000 ${data_path}/group_level_n${n}_${run}_${type}.gfeat/${cope}.feat/stats/zstat1.nii.gz $min $max ${cope}_overlay_t2
		#overlay 0 1 ${data_path}/masks/template_t2s_cropped_cord.nii.gz 300 800 ${data_path}/ses-spinalcord_task-${task}_N28_age_sex_cov2.3_fixed_corrected_masked.gfeat/${cope}.feat/thresh_zstat1.nii.gz 2.3 6.8 ${data_path}/ses-spinalcord_task-${task}_N28_age_sex_cov2.3_fixed_corrected_masked.gfeat/${cope}.feat/thresh_zstat2.nii.gz 2.3 6.8 ${cope}_overlay
		fslroi ${cope}_overlay ${cope}_overlay 15 47 22 32 0 -1
		fslroi ${cope}_overlay_t2 ${cope}_overlay_t2 12 51 0 -1 35 190

		# Create coronal slices y=36
		slicer ${cope}_overlay_t2 -u -y -36  ${cope}_y_36_${type}_${run}.png
		#convert ${task}_${cope}_y_36.png -crop 33x20+1+122 crop.png

		for slice in ${spinal_cord_slices[@]}; do
			slicer ${cope}_overlay -u -z -${slice} ${task}_${cope}_z_${slice}.png
			#mv ${task}_${cope}_z_${slice}.png crop.png
			convert ${task}_${cope}_z_${slice}.png -crop 47x36+0+111 crop.png
			mv crop.png ${task}_${cope}_z_${slice}.png
		done

		pngappend ${task}_${cope}_z_190.png - ${task}_${cope}_z_180.png - ${task}_${cope}_z_170.png - ${task}_${cope}_z_160.png - ${task}_${cope}_z_150.png - ${task}_${cope}_z_140.png - ${task}_${cope}_z_130.png - ${task}_${cope}_z_120.png - ${task}_${cope}_z_110.png - ${task}_${cope}_z_100.png - ${task}_${cope}_z_90.png - ${task}_${cope}_z_80.png - ${task}_${cope}_z_70.png - ${task}_${cope}_z_60.png - ${task}_${cope}_z_50.png - ${task}_${cope}_z_40.png ${cope}_${type}_${run}.png


		rm ${task}_${cope}_z*.png
		rm ${cope}_overlay.nii.gz
		mv ${cope}_${type}_${run}.png ${output_path}/n${n}_${type}/
		mv ${cope}_y_36_${type}_${run}.png ${output_path}/n${n}_${type}/
	done
done
