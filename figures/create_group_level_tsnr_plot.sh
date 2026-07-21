#!/bin/sh
# 
#
# 
#Initialization of parameters
data_path=/home/sbedard/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/
spinal_cord_slices=($(seq 50 10 190))
echo ${spinal_cord_slices[@]}
rm -f tsnr_values.txt
runs=(rightthumb leftthumb rightmiddle leftmiddle rightpinky leftpinky)
tsnr_map=${data_path}/preprocessing_ALL/results/tsnr_maps_n25/mean_tsnr_PAM50.nii.gz
#tsnr_map=${data_path}/preprocessing_ALL/results/tsnr_maps_n25/mean_tsnr_PAM50_run-rightpinky.nii.gz

#overlay 0 1 ${data_path}/masks/template_t2s_cropped_cord.nii.gz 300 800 ${data_path}/tsnr_n40/mean_tsnr_PAM50.nii.gz 10 25 tsnr_overlay.nii.gz
fslroi ${tsnr_map}  mean_tsnr_crop.nii.gz 32 75 34 75 691 263
overlay 0 1 ${data_path}/masks/template_t2s_cropped_cord.nii.gz 300 800 mean_tsnr_crop.nii.gz 12 25 tsnr_overlay.nii.gz
#overlay 0 1 mean_tsnr_crop.nii.gz 10 25 mean_tsnr_crop.nii.gz 0 25 tsnr_overlay.nii.gz
fslroi tsnr_overlay tsnr_overlay 22 33 28 20 0 -1

# Extract mean tSNR values within the cord mask
fslroi $SCT_DIR/data/PAM50/template/PAM50_cord.nii.gz  PAM50_cord_crop.nii.gz 32 75 34 75 691 263
sct_maths -i mean_tsnr_crop.nii.gz -mul PAM50_cord_crop.nii.gz -o mean_tsnr_crop_mask.nii.gz

echo slice tsnr >> tsnr_values.txt

for slice in ${spinal_cord_slices[@]}; do
    echo ${slice}
    slicer tsnr_overlay -u -z -${slice} tsnr_z_${slice}.png
    convert tsnr_z_${slice}.png -crop 33x20+1+122 crop.png
    mv crop.png tsnr_z_${slice}.png
    fslroi mean_tsnr_crop_mask.nii.gz mean_tsnr_crop_mask_z${slice}.nii.gz 0 -1 0 -1 $slice 1 
    tsnr=`fslstats mean_tsnr_crop_mask_z${slice}.nii.gz -M`
    #tsnr=`fslstats mean_tsnr_crop_mask_z.nii.gz -k ${data_path}/masks/mask_cord_N40.nii.gz -l ${slice} -u ${slice}`
    echo ${slice} ${tsnr}
    echo ${slice} ${tsnr} >> tsnr_values.txt

done

pngappend tsnr_z_190.png '-' tsnr_z_180.png '-' tsnr_z_170.png '-' tsnr_z_160.png '-' tsnr_z_150.png '-' tsnr_z_140.png '-' tsnr_z_130.png '-' tsnr_z_120.png '-' tsnr_z_110.png '-' tsnr_z_100.png '-' tsnr_z_90.png '-' tsnr_z_80.png '-' tsnr_z_70.png '-' tsnr_z_60.png '-' tsnr_z_50.png tsnr.png

mv tsnr.png ${data_path}/preprocessing_ALL/results/tsnr_maps_n25/tsnr.png
mv tsnr_values.txt ${data_path}/preprocessing_ALL/results/tsnr_maps_n25/tsnr_values.txt

rm tsnr_z*.png
rm tsnr_overlay.nii.gz
rm mean_tsnr_crop_mask_z*.nii.gz
rm mean_tsnr_crop_mask.nii.gz
rm mean_tsnr_crop.nii.gz
		
