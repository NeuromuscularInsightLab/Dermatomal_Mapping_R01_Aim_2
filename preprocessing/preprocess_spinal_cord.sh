#!/bin/bash
#
# Analyses spinal cord data for the Dermatomal Mapping R01 project.
#
# Usage:
#     sct_run_batch -c <PATH_TO_REPO>/etc/config_process_data.json  # TODO
#
# The following global variables are retrieved from the caller sct_run_batch
# but could be overwritten by uncommenting the lines below:
# PATH_DATA_PROCESSED="~/data_processed"
# PATH_RESULTS="~/results"
# PATH_LOG="~/log"
# PATH_QC="~/qc"
#
#
#
# Manual segmentations or labels should be located under:
# PATH_DATA/derivatives/labels/SUBJECT/ses-0X/anat/
#
#
#
# Authors: Sandrine Bédard, Kenneth Weber and Merve Kaptan
#

# Uncomment for full verbose
set -x

# Immediately exit if error
#set -e -o pipefail  # comment to not skip

# Exit if user presses CTRL+C (Linux) or CMD+C (OSX)
trap "echo Caught Keyboard Interrupt within script. Exiting now.; exit" INT

# Print retrieved variables from sct_run_batch to the log (to allow easier debug)
echo "Retrieved variables from from the caller sct_run_batch:"
echo "PATH_DATA: ${PATH_DATA}"
echo "PATH_DATA_PROCESSED: ${PATH_DATA_PROCESSED}"
echo "PATH_RESULTS: ${PATH_RESULTS}"
echo "PATH_LOG: ${PATH_LOG}"
echo "PATH_QC: ${PATH_QC}"
echo "PATH_SEGMANUAL: ${PATH_SEGMANUAL}"
# Get path derivatives
path_source=$(dirname $PATH_DATA)
# Get path of script repository
PATH_SCRIPTS=$PWD


# CONVENIENCE FUNCTIONS
# ======================================================================================================================
segment_if_does_not_exist() {
  ###
  #  This function checks if a manual spinal cord segmentation file already exists, then:
  #    - If it does, copy it locally.
  #    - If it doesn't, perform automatic spinal cord segmentation
  #  This allows you to add manual segmentations on a subject-by-subject basis without disrupting the pipeline.
  ###
  local file="$1"
  local contrast="$2"
  local segmentation_method="$3"  # deepseg or propseg
  local subfolder="$4"
  # Update global variable with segmentation file name
  FILESEG="${file}_label-SC_seg"
  FILESEGMANUAL="${PATH_SEGMANUAL}/${SUBJECT}/${subfolder}/${FILESEG}.nii.gz"
  echo
  echo "Looking for manual segmentation: $FILESEGMANUAL"
  if [[ -e $FILESEGMANUAL ]]; then
    echo "Found! Using manual segmentation."
    rsync -avzh $FILESEGMANUAL ${FILESEG}.nii.gz
    ${SCT_EXEC}sct_qc -i ${file}.nii.gz -s ${FILESEG}.nii.gz -p sct_deepseg_sc -qc ${PATH_QC} -qc-subject ${SUBJECT}
  else
    echo "Not found. Proceeding with automatic segmentation."
    # Segment spinal cord
    if [[ $segmentation_method == 'deepseg' ]];then
        ${SCT_EXEC}sct_deepseg spinalcord -i ${file}.nii.gz -largest 1 -o ${file}_label-SC_seg.nii.gz -qc ${PATH_QC} -qc-subject ${SUBJECT}
    elif [[ $segmentation_method == 'propseg' ]]; then
        ${SCT_EXEC}sct_propseg -i ${file}.nii.gz -c ${contrast} -qc ${PATH_QC} -qc-subject ${SUBJECT} -CSF
    elif [[ $segmentation_method == 'epi' ]]; then
        ${SCT_EXEC}sct_deepseg sc_epi -i ${file}.nii.gz -o ${file}_label-SC_seg.nii.gz -qc ${PATH_QC} -qc-subject ${SUBJECT}
        # Copy header of original image to ensure that pixdim stays the same
        fslcpgeom ${file}.nii.gz ${file}_label-SC_seg.nii.gz 

    fi
  fi
}


label_if_does_not_exist(){
  ###
  #  This function checks if a manual labels exists, then:
  #    - If it does, copy it locally and use them to initialize vertebral labeling
  #    - If it doesn't, perform automatic vertebral labeling
  ###
  local file="$1"
  local file_seg="$2"
  # Update global variable with segmentation file name
  FILELABEL="${file}_label-disc"
  FILELABELMANUAL="${PATH_SEGMANUAL}/${SUBJECT}/anat/${FILELABEL}.nii.gz"
  echo "Looking for manual label: $FILELABELMANUAL"
  if [[ -e $FILELABELMANUAL ]]; then
    echo "Found! Using manual labels."
    rsync -avzh $FILELABELMANUAL ${FILELABEL}.nii.gz
    # Generate labeled segmentation from manual disc labels
    ${SCT_EXEC}sct_label_vertebrae -i ${file}.nii.gz -s ${file_seg}.nii.gz -discfile ${FILELABEL}.nii.gz -c t2 -qc ${PATH_QC} -qc-subject ${SUBJECT}
  else
    echo "Not found. Proceeding with automatic labeling."
    # Generate vertebral labeling
    ${SCT_EXEC}sct_label_vertebrae -i ${file}.nii.gz -s ${file_seg}.nii.gz -c t2 -qc ${PATH_QC} -qc-subject ${SUBJECT}
  fi
}


segment_rootlets_if_does_not_exist() {
  ###
  #  This function checks if a manual spinal nerve rootlets segmentation file already exists, then:
  #    - If it does, copy it locally.
  #    - If it doesn't, perform automatic spinal nerve rootlets segmentation
  ###
  local file="$1"
  local file_seg="$2"
  # Update global variable with segmentation file name
  FILEROOTLET="${file}_label-rootlets_dseg"
  FILESEGMANUAL="${PATH_SEGMANUAL}/${SUBJECT}/anat/${FILEROOTLET}.nii.gz"
  echo
  echo "Looking for manual segmentation: $FILESEGMANUAL"
  if [[ -e $FILESEGMANUAL ]]; then
    echo "Found! Using manual segmentation."
    rsync -avzh $FILESEGMANUAL ${FILEROOTLET}.nii.gz
  else
    echo "Not found. Proceeding with automatic segmentation."
    # Segment spinal nerve rootlets
    ${SCT_EXEC}sct_deepseg rootlets -i ${file}.nii.gz -o ${FILEROOTLET}.nii.gz -qc ${PATH_QC} -qc-subject ${SUBJECT}
  fi
}


# Retrieve input params and other params
SUBJECT=$1
REG=$2
REG=$2
#tasks="${@:2}"
# echo "Tasks:"
# echo $tasks

# get starting time:
start=`date +%s`


# SCRIPT STARTS HERE
# ==============================================================================
# Display useful info for the log, such as SCT version, RAM and CPU cores available
${SCT_EXEC}sct_check_dependencies -short

# Go to folder where data will be copied and processed
cd $PATH_DATA_PROCESSED


# TODO:

# if [[ -f ${HOME}/anaconda3/etc/profile.d/conda.sh ]]; then
#   source ${HOME}/anaconda3/etc/profile.d/conda.sh
# elif [[ -f ${HOME}/Miniconda3/etc/profile.d/conda.sh ]]; then
#   source ${HOME}/Miniconda3/etc/profile.d/conda.sh
# else
#   echo Python not installed. Exit program.
#   exit 1
# fi

# #Activate conda environment
# source ${HOME}/anaconda3/etc/profile.d/conda.sh
# #eval "$(conda shell.bash hook)"
# conda activate Dermatomal_Mapping_R01

# Copy source images
# Note: we use '/./' in order to include the sub-folder 'ses-0X'
rsync -Ravzh $PATH_DATA/./$SUBJECT .

cd ${SUBJECT}/anat

# Define variables
# We do a substitution '/' --> '_' in case there is a subfolder 'ses-0X/'
file="${SUBJECT//[\/]/_}"

# Get session
SES=$(basename "$SUBJECT")
# get subject name without session
sub_id=$(dirname "$SUBJECT")

# Only include spinal cord sessions
if [[ $SES == *"spinalcord"* ]];then
    # -------------------------------------------------------------------------
    # T2w
    # -------------------------------------------------------------------------

    # Add suffix corresponding to contrast
    file_t2w=${file}_acq-cervical_T2w
    # Check if T2w image exists
    if [[ -f ${file_t2w}.nii.gz ]];then
          # Create directory for T2w results
          mkdir -p ${PATH_DATA_PROCESSED}/${SUBJECT}/anat/T2w
          cp ${file_t2w}.nii.gz ${PATH_DATA_PROCESSED}/${SUBJECT}/anat/T2w
          cd T2w
          
          # Spinal cord segmentation
          # Note: For T2w images, we use sct_deepseg_sc with 2 kernel. Generally, it works better than sct_propseg and sct_deepseg_sc with 3d kernel.
          segment_if_does_not_exist ${file_t2w} 't2' 'deepseg' 'anat'
          file_t2_seg="${file_t2w}_label-SC_seg"

          # Vertebral labeling 
          label_if_does_not_exist ${file_t2w} ${file_t2_seg}
          file_t2_labels="${file_t2w}_label-SC_seg_labeled"
          file_t2_labels_discs="${file_t2w}_label-SC_seg_labeled_discs"

          # Extract dics 1 to 10 for registration to template (C1 to T2-T3)
          ${SCT_EXEC}sct_label_utils -i ${file_t2_labels_discs}.nii.gz -keep 1,2,3,4,5,6,7,8,9,10 -o ${file_t2_labels_discs}_1to10.nii.gz
          file_t2_labels_discs="${file_t2w}_label-SC_seg_labeled_discs_1to10"
          
          # Label spinal nerve rootlets
          segment_rootlets_if_does_not_exist ${file_t2w} ${file_t2_seg}
          file_t2_rootlets="${file_t2w}_label-rootlets_dseg"
          # Create center-of-mass for QC purpose
          ${SCT_EXEC}sct_label_utils -i ${file_t2_rootlets}.nii.gz -cubic-to-point -o ${file_t2_rootlets}_mid.nii.gz
          ${SCT_EXEC}sct_label_utils -i ${file_t2_seg}.nii.gz -project-centerline ${file_t2_rootlets}_mid.nii.gz  -o ${file_t2_rootlets}_mid_center.nii.gz
          ${SCT_EXEC}sct_qc -i ${file_t2w}.nii.gz  -s ${file_t2_rootlets}_mid_center.nii.gz -p sct_label_utils -qc $PATH_QC -qc-subject ${SUBJECT}


          # Register to template using disc labels or spinal rootlets
          if [[ $REG == *"disc"* ]]; then
            ${SCT_EXEC}sct_register_to_template -i ${file_t2w}.nii.gz -s ${file_t2_seg}.nii.gz -ldisc ${file_t2_labels_discs}.nii.gz -c t2 -qc ${PATH_QC} -qc-subject ${SUBJECT}
          else
            ${SCT_EXEC}sct_register_to_template -i ${file_t2w}.nii.gz -s ${file_t2_seg}.nii.gz -lrootlet ${file_t2_rootlets}.nii.gz -c t2 -qc ${PATH_QC} -qc-subject ${SUBJECT}
            ${SCT_EXEC}sct_register_to_template -i ${file_t2w}.nii.gz -s ${file_t2_seg}.nii.gz -ldisc ${file_t2_labels_discs}.nii.gz -ofolder reg_discs -c t2 -qc ${PATH_QC} -qc-subject ${SUBJECT}
          fi
          cd ..
    else
          echo Skipping T2w
    fi
 

    # -------------------------------------------------------------------------
    # FUNC
    # -------------------------------------------------------------------------
    cd ../func

  
    runs=(rightthumb leftthumb rightmiddle leftmiddle rightpinky leftpinky)

    for run in "${runs[@]}";do

      cd ${PATH_DATA_PROCESSED}/${SUBJECT}/func/
      file_task=${file}_task-tens_run-${run}_bold
      file_physio=${file}_task-tens_run-${run}_physio
      if [[ -f ${file_task}.nii.gz ]];then
          # Create output path for run
          mkdir -p ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}
          # Copy image & physio inside folder
          cp ${file_task}.nii.gz ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}/
          cp ${file_physio}.physio ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}/
          # Go inside folder
          cd "run-${run}"
          # Create folder for PNM
          mkdir -p ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}/PNM_run-${run}/

          # Remove dummy volumes
          echo "Number of volumes before"
          echo $(fslval ${file_task} dim4)
          if [ $(fslval ${file_task} dim4) == 137 ]; then
            fslroi ${file_task} ${file_task} 3 -1
          fi
          # Get dims
          number_of_volumes=$(fslval ${file_task} dim4)
          tr=$(fslval ${file_task} pixdim4)

          # Compute mean image
          ${SCT_EXEC}sct_maths -i ${file_task}.nii.gz -mean t -o ${file_task}_mean.nii.gz
          file_task_mean="${file_task}_mean"
          
          # Create mask if doesn't exist:
          FILE_MASK="${PATH_SEGMANUAL}/${SUBJECT}/func/${file_task_mean}_mask.nii.gz"
          echo
          echo "Looking for manual spinal mask: $FILE_MASK"
          if [[ -e $FILE_MASK ]]; then
            echo "Found! Using manual segmentation."
            rsync -avzh $FILE_MASK "${file_task_mean}_mask.nii.gz"
          else
            # Segment the spinal cord
            segment_if_does_not_exist ${file_task_mean} 't2s' 'epi' 'func'
            # Dilate the spinal cord mask
            ${SCT_EXEC}sct_maths -i ${file_task_mean}_label-SC_seg.nii.gz -dilate 8 -shape disk -o ${file_task_mean}_mask.nii.gz -dim 2
          fi
          # Qc of mask
          ${SCT_EXEC}sct_qc -i ${file_task_mean}.nii.gz -p sct_deepseg_sc -qc ${PATH_QC} -s ${file_task_mean}_mask.nii.gz -qc-subject ${SUBJECT}
          ${SCT_EXEC}sct_fmri_compute_tsnr -i ${file_task}.nii.gz -o ${file_task}_tsnr.nii.gz
          if [[ ! -f ${file_task}_mc2.nii.gz ]]; then
            # --------------------
            # 2D Motion correction
            # --------------------
            # Step 1 of 2D motion correction using mid volume
            # Select mid volume
            mid_volume=$(($number_of_volumes / 2))
            fslroi ${file_task} ${file_task}_mc1_ref $mid_volume 1
            # Apply motion correction
            ${PATH_SCRIPTS}/2D_slicewise_motion_correction.sh -i ${file_task}.nii.gz -r ${file_task}_mc1_ref.nii.gz -m ${file_task_mean}_mask.nii.gz -o mc1
            
            # Step 2 of 2D motion correction using mean of mc1 as ref
            # Create mask if doesn't exist:
            FILE_MASK="${PATH_SEGMANUAL}/${SUBJECT}/func/${file_task}_mc1_mask.nii.gz"
            # ${file_task}_mc1_mask.nii.gz
            echo
            echo "Looking for manual spinal mask: $FILE_MASK"
            if [[ -e $FILE_MASK ]]; then
              echo "Found! Using manual segmentation."
              rsync -avzh $FILE_MASK "mc1_mask.nii.gz"
            else
            # Segment the spinal cord
              segment_if_does_not_exist mc1_mean 't2s' 'epi' 'func'
              # check dilating
              ${SCT_EXEC}sct_maths -i mc1_mean_label-SC_seg.nii.gz -dilate 8 -shape disk -o mc1_mask.nii.gz -dim 2
              # Qc of mask
              ${SCT_EXEC}sct_qc -i  mc1_mean.nii.gz -p sct_deepseg_sc -qc ${PATH_QC} -s mc1_mask.nii.gz -qc-subject ${SUBJECT}
            fi
            # Apply motion correction step 2
            ${PATH_SCRIPTS}/2D_slicewise_motion_correction.sh -i mc1.nii.gz -r mc1_mean.nii.gz -m mc1_mask.nii.gz -o mc2

            mv mc2.nii.gz ${file_task}_mc2.nii.gz
            mv mc2_mean.nii.gz ${file_task}_mc2_mean.nii.gz
            mv mc2_tsnr.nii.gz ${file_task}_mc2_tsnr.nii.gz
            mv mc2_mat.tar.gz ${file_task}_mc2_mat.tar.gz

            # Move motion regressors to .PNM
            mv Rz.nii.gz ./PNM_run-${run}
            mv Tx.nii.gz ./PNM_run-${run}
            mv Ty.nii.gz ./PNM_run-${run}

            # Create QC report for TSNR:
            ${SCT_EXEC}sct_qc -i ${file_task}_tsnr.nii.gz -d ${file_task}_mc2_tsnr.nii.gz -s ${file_task_mean}_label-SC_seg.nii.gz -p sct_fmri_compute_tsnr -qc ${PATH_QC} -qc-subject ${SUBJECT}
          fi
          # Create spinal cord mask and spinal canal mask
          file_task_mc2=${file_task}_mc2
          file_task_mc2_mean=${file_task}_mc2_mean

          FILE_SPINAL_CANAL_SEG="${PATH_SEGMANUAL}/${SUBJECT}/func/${file_task_mc2_mean}_label-canal_seg.nii.gz"
          echo
          echo "Looking for manual spinal canal segmentation: $FILE_SPINAL_CANAL_SEG"
          if [[ -e $FILE_SPINAL_CANAL_SEG ]]; then
            echo "Found! Using manual segmentation."
            rsync -avzh $FILE_SPINAL_CANAL_SEG "${file_task_mc2_mean}_label-canal_seg.nii.gz"
          else
            echo "No manual spinal canal segmentation found in the derivatives. Running automatic segmentation."
            segment_if_does_not_exist ${file_task_mc2_mean} 't2s' 'propseg' 'anat'
            ${SCT_EXEC}sct_maths -i ${file_task_mc2_mean}_seg.nii.gz -add ${file_task_mc2_mean}_CSF_seg.nii.gz -o ${file_task_mc2_mean}_label-canal_seg.nii.gz

          fi
      # Change dtype:
      ${SCT_EXEC}sct_image -i ${file_task_mc2_mean}_label-canal_seg.nii.gz -type uint8
      # Qc of Spinal canal segmentation
      ${SCT_EXEC}sct_qc -i ${file_task_mc2_mean}.nii.gz -p sct_deepseg_sc -qc ${PATH_QC} -s ${file_task_mc2_mean}_label-canal_seg.nii.gz -qc-subject ${SUBJECT}

      # Create segmentation using sct_deepseg

      # Test EPI seg --> select the best
      segment_if_does_not_exist ${file_task_mc2_mean} 't2' 'epi' 'func'
      # Segment spinal cord after motion correction
      #segment_if_does_not_exist ${file_task_mc2_mean} 't2' 'deepseg' 'func'

      file_task_mc2_mean_seg="${file_task_mc2_mean}_label-SC_seg"

      # QC for motion correction
      ${SCT_EXEC}sct_qc -i ${file_task_mc2}.nii.gz -p sct_fmri_moco -qc ${PATH_QC} -s ${file_task_mc2_mean_seg}.nii.gz -d  ${file_task}.nii.gz -qc-subject ${SUBJECT}

      # Register to T2w image
      ${SCT_EXEC}sct_register_multimodal -i ${SCT_DIR}/data/PAM50/template/PAM50_t2.nii.gz -iseg ${SCT_DIR}/data/PAM50/template/PAM50_cord.nii.gz -d ${file_task_mc2_mean}.nii.gz -dseg ${file_task_mc2_mean_seg}.nii.gz -param step=1,type=seg,algo=centermass:step=2,type=seg,algo=bsplinesyn,metric=MeanSquares,slicewise=1,iter=3:step=3,type=im,algo=syn,metric=CC,iter=1,slicewise=1 -initwarp ../../anat/T2w/warp_template2anat.nii.gz -initwarpinv ../../anat/T2w/warp_anat2template.nii.gz -qc ${PATH_QC} -qc-subject ${SUBJECT}
      
      # Warp to template (do we want the spinal levels ?? if so add -s 1)
      if [[ $REG == *"disc"* ]]; then
        ${SCT_EXEC}sct_warp_template -d ${file_task_mc2_mean}.nii.gz -w warp_PAM50_t22${file_task_mc2_mean}.nii.gz -qc ${PATH_QC} -qc-subject ${SUBJECT}
      else
        # Use discs registration instead to make sure WM covers all slices
        ${SCT_EXEC}sct_register_multimodal -i ${SCT_DIR}/data/PAM50/template/PAM50_t2.nii.gz -iseg ${SCT_DIR}/data/PAM50/template/PAM50_cord.nii.gz -d ${file_task_mc2_mean}.nii.gz -dseg ${file_task_mc2_mean_seg}.nii.gz -param step=1,type=seg,algo=centermass:step=2,type=seg,algo=bsplinesyn,metric=MeanSquares,slicewise=1,iter=3:step=3,type=im,algo=syn,metric=CC,iter=1,slicewise=1 -initwarp ../../anat/T2w/reg_discs/warp_template2anat.nii.gz -initwarpinv ../../anat/T2w/reg_discs/warp_anat2template.nii.gz -qc ${PATH_QC} -qc-subject ${SUBJECT}  -ofolder reg_discs
        ${SCT_EXEC}sct_warp_template -d ${file_task_mc2_mean}.nii.gz -w reg_discs/warp_PAM50_t22${file_task_mc2_mean}.nii.gz -qc ${PATH_QC} -qc-subject ${SUBJECT}
      fi
      # Create CSF regressor
      file_task_mc2=${file_task}_mc2  # to remove
      # Create CSF mask form spinal cord seg and spinal canal seg
      fslmaths ${file_task_mc2_mean_seg} -binv temp_mask
      fslmaths ${file_task_mc2}_mean_label-canal_seg -mul temp_mask ${file_task_mc2}_csf_mask
      rm temp_mask.nii.gz
      ${PATH_SCRIPTS}/create_slicewise_regressor_from_mask.sh -i ${file_task_mc2}.nii.gz -m ${file_task_mc2}_csf_mask.nii.gz -o csf_regressor
      mv ${file_task_mc2}_csf_regressor.nii.gz ./PNM_run-${run}

      # Create WM regressor
      fslmaths ./label/template/PAM50_wm.nii.gz -thr 0.9 -bin ${file_task_mc2}_wm_mask
      ${PATH_SCRIPTS}/create_slicewise_regressor_from_mask.sh -i ${file_task_mc2}.nii.gz -m ${file_task_mc2}_wm_mask.nii.gz -o wm_regressor
      mv ${file_task_mc2}_wm_regressor.nii.gz ./PNM_run-${run}


      #Process physio
      if [[ -e ${file_physio}.physio ]]; then
        FILE_PHYSIO_CARD="${PATH_SEGMANUAL}/${SUBJECT}/func/${file_physio}_peak.txt"
        echo starting physio

        echo "Looking for manual peak detection: $FILE_PHYSIO_CARD"
        if [[ -e $FILE_PHYSIO_CARD ]]; then
          echo "Found! Using manual segmentation."
          rsync -avzh $FILE_PHYSIO_CARD "${file_physio}_peak.txt"
        else
          echo "No manual physio file found in the derivatives. Please running peak detection"
        fi
    	  popp -i ${file_physio}_peak.txt -o physio -s 100 --tr=${tr} --smoothcard=0.1 --smoothresp=0.1 --resp=2 --cardiac=5 --trigger=3 -v --pulseox_trigger
        # Run PNM using manual peak detections in derivatives
        pnm_evs -i ${file_task}.nii.gz -c physio_card.txt -r physio_resp.txt -o physio_ --tr=${tr} --oc=4 --or=4 --multc=2 --multr=2 --sliceorder=interleaved_up

      fi
      mv physio* ./PNM_run-${run}
      ls ${PWD}/PNM_run-${run}/*.nii.gz > ./PNM_run-${run}/${file_task}_physio_evlist.txt # Create ev list
      cp ${PATH_SCRIPTS}/spinal_cord_pnm.fsf ./
      export PATH_DATA_PROCESSED SUBJECT file_task run tr number_of_volumes
      envsubst < "spinal_cord_pnm.fsf" > "spinal_cord_pnm_${file_task}.fsf"
      # Remove existing feat repo if already exists
      if [[ -d "${file_task_mc2}_pnm.feat" ]]; then
        rm -r "${file_task_mc2}_pnm.feat"
      fi
      feat "spinal_cord_pnm_${file_task}.fsf"

      # Create denoised image
      fslmaths ./${file_task_mc2}_pnm.feat/stats/res4d.nii.gz -add ./${file_task_mc2}_pnm.feat/mean_func.nii.gz ${file_task_mc2}_pnm
      #tr=$(fslval ${file_task_mc2} pixdim4) # Get TR of volumes
      fslsplit ${file_task_mc2}_pnm vol -t
      v=vol????.nii.gz
      fslmerge -tr ${file_task_mc2}_pnm ${v} ${tr}
      rm $v

      # Find motion outliers
      fsl_motion_outliers -i ${file_task_mc2} -m ${file_task_mc2_mean_seg} --dvars --nomoco -o ${file_task}_motion_outliers.txt #removed the term dvars to make it compatible with brain naming

      # If file does not exist, create an empty file, otherwise FSL crashes
      file_outliers="${file_task}_motion_outliers.txt"
      
      if [[ ! -f "$file_outliers" ]]; then
            confoundevs=0
      else
            confoundevs=1
      fi

      #slice_timing after PNM
      slicetimer -i ${file_task_mc2}_pnm -o ${file_task_mc2}_pnm_stc --repeat=${tr} --odd  # interleaved ascending (bottom-up)
  

      # Warp 4D to template
            # Warp each volume to the template
      fslsplit ${file_task_mc2}_pnm_stc vol -t
      tr=`fslval ${file_task_mc2}_pnm_stc pixdim4` # Get TR of volumes
      tdimi=`fslval ${file_task_mc2}_pnm_stc dim4` # Get the number of volumes
      last_volume=$(echo "scale=0; $tdimi-1" | bc) # Find index of last volume
      for ((k=0; k<=$last_volume; k++));do
          vol="$(printf "vol%04d" ${k})"
          ${SCT_EXEC}sct_apply_transfo -i ${vol}.nii.gz -d ${SCT_DIR}/data/PAM50/template/PAM50_t2.nii.gz -w warp_${file_task_mc2_mean}2PAM50_t2.nii.gz -o ${vol}2template.nii.gz -x spline
          #fslmaths ${vol}2template.nii.gz -mul ${SCT_EXEC}${SCT_DIR}/data/PAM50/template/PAM50_cord.nii.gz ${vol}2template.nii.gz
          ${SCT_EXEC}sct_maths -i ${vol}2template.nii.gz -mul ${SCT_DIR}/data/PAM50/template/PAM50_cord.nii.gz -o ${vol}2template.nii.gz
          fslroi ${vol}2template.nii.gz ${vol}2template.nii.gz 32 75 34 75 691 263
      done
      v="vol????2template.nii.gz"
      fslmerge -tr ${file_task_mc2}_pnm_stc2template $v $tr # Merge warped volumes together
      rm $v
      v=vol????.nii.gz
      rm $v
      #${SCT_EXEC}sct_apply_transfo -i ${file_task_mc2}_pnm_stc.nii.gz -d ${SCT_DIR}/data/PAM50/template/PAM50_t2.nii.gz -w warp_${file_task_mc2_mean}2PAM50_t2.nii.gz -o ${file_task_mc2}_pnm_stc2template.nii.gz -x spline
      
      #fslmaths ${file_task_mc2}_pnm_stc2template.nii.gz -mul ${SCT_EXEC}${SCT_DIR}/data/PAM50/template/PAM50_cord.nii.gz ${file_task_mc2}_pnm_stc2template.nii.gz
      #fslroi ${file_task_mc2}_pnm_stc2template.nii.gz ${file_task_mc2}_pnm_stc2template.nii.gz 32 75 34 75 691 263

      # Remove outside voxels based on spinal cord mask z limits
      ${SCT_EXEC}sct_apply_transfo -i ${file_task_mc2_mean_seg}.nii.gz -d ${SCT_DIR}/data/PAM50/template/PAM50_t2.nii.gz -w warp_${file_task_mc2_mean}2PAM50_t2.nii.gz -o ${file_task_mc2_mean_seg}2template.nii.gz -x nn
      fslroi ${file_task_mc2_mean_seg}2template.nii.gz ${file_task_mc2_mean_seg}2template.nii.gz 32 75 34 75 691 263
      fslmaths ${file_task_mc2_mean_seg}2template.nii.gz -kernel 2 -dilD -dilD -dilD -dilD -dilD temp_mask
      fslmaths ${file_task_mc2}_pnm_stc2template -mul temp_mask ${file_task_mc2}_pnm_stc2template
      rm temp_mask.nii.gz
      # Smoothing 2x2x5 mm
      #sigma= 2mm/2.354 = | sigma = 5m/2.354 for 2mm and 5 mm of full width at half maximum (FWHM)
      fslmaths ${file_task_mc2}_pnm_stc2template.nii.gz -s 0.85,0.84,2.124 ${file_task_mc2}_pnm_stc2template_smooth225.nii.gz
      
      # Run first-level analysis
      ###############################
     #rsync the folder fsl_stim_vectors:
      #PATH_VECTORS="${PATH_SEGMANUAL}/${SUBJECT}/func/fsl_stim_vectors/"
      PATH_BIOPAC="$(dirname "$PATH_SCRIPTS")"
      PATH_VECTORS="${PATH_BIOPAC}/biopac/fsl_stim_vectors"
      echo ${PATH_VECTORS}
      stim_acq_file=$(ls -1 "${PATH_SEGMANUAL}/${SUBJECT}/biopac/${sub_id}_task-tens_run-${run}_acq"*.acq)
      echo ${stim_acq_file}
      if [[ -e ${stim_acq_file} ]]; then
        rsync -avzh ${stim_acq_file} ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}/
      else
        echo "No stim acq file found in the derivatives."
      fi
      #Get the stim parameter to cp the correct stim files:
      stim_acq_file="$(basename "$stim_acq_file")"
      stim_parameters=`echo ${stim_acq_file} | awk -F 'acq-' '{print $2}' | awk -F '.acq' '{print $1}'`
      # Create variable with filename to  min max of amp and export to feat
      # If fsl_stim_vectors folder exists, remove it
      if [[ -d fsl_stim_vectors ]]; then
        rm -rf fsl_stim_vectors
      fi
      mkdir -p fsl_stim_vectors
      if [[ -d ${PATH_VECTORS} ]]; then
        cp ${PATH_VECTORS}/*${stim_parameters}*.txt ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}/fsl_stim_vectors/
        # todo rsync
      else
        echo "fsl_stim_vectors not found."
      fi
      cd fsl_stim_vectors
      # Add subject if in name:
      for file_stim in *.txt; do
          mv ${file_stim} ${sub_id}_${file_stim}
      done
      #update stim_parameters variable to get the correct file name for feat
      stim_file=$(ls -1 *_stim_1.txt)
      stim_parameters=`echo ${stim_file} | awk -F 'fsl_stim_vector_' '{print $2}' | awk -F 'hz_stim' '{print $1}'`

      cd ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}
      echo ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}

      func_data="${file_task}_mc2_pnm_stc2template_smooth225" #TODO
      subject=${sub_id}
      analysis_path=$PATH_DATA_PROCESSED/${subject}
      region="spinalcord"
      session="" # TODO change if multiple sessions
      smoothing=0
      coil="" # TODO add coil info if needed

      cd ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}
      #Run first-level trialwise analysis
      # Remove existing feat repo if already exists
      if [[ -d "${func_data}_trialwise_first_level.feat" ]]; then
        rm -r "${func_data}_trialwise_first_level.feat"
      fi

      export analysis_path subject coil session run func_data region tr number_of_volumes stim_parameters smoothing confoundevs
      envsubst < "${PATH_SCRIPTS}/first_level_trialwise.fsf" > "${func_data}_first_level_trialwise.fsf"
	    feat ${func_data}_first_level_trialwise.fsf

      #Run registration for first level trialwise analysis
      cd ${func_data}_trialwise_first_level.feat
      mkdir -p reg
      cp /usr/local/fsl/etc/flirtsch/ident.mat reg/example_func2standard.mat
      cp example_func.nii.gz reg/example_func.nii.gz
      cp $SCT_DIR/data/PAM50/template/PAM50_t2s.nii.gz reg/standard.nii.gz
      fslmaths reg/standard.nii.gz -mas $SCT_DIR/data/PAM50/template/PAM50_cord.nii.gz reg/standard_masked.nii.gz
      fslroi reg/standard_masked.nii.gz reg/standard.nii.gz 32 75 34 75 691 263

      cd ${PATH_DATA_PROCESSED}/${SUBJECT}/func/run-${run}

      #Run second-level trialwise analysis
      # Remove existing feat repo if already exists
      if [[ -d "${func_data}_trialwise_second_level.gfeat" ]]; then
        rm -r "${func_data}_trialwise_second_level.gfeat"
      fi
      export analysis_path subject coil session run func_data region tr number_of_volumes stim_parameters smoothing
      envsubst < "${PATH_SCRIPTS}/second_level_trialwise.fsf" > "${func_data}_second_level_trialwise.fsf"
	    feat ${func_data}_second_level_trialwise.fsf
      echo $PWD
      cd ..
    fi
  done
  
fi

#Copy PAM50 template for masking the group level results
cp $SCT_DIR/data/PAM50/template/PAM50_cord.nii.gz PAM50_cord.nii.gz
fslroi PAM50_cord.nii.gz PAM50_cord_cropped.nii.gz 32 75 34 75 691 263


# subject=$(dirname "$SUBJECT")
# analysis_path=$PATH_DATA_PROCESSED/${subject}
# region="spinalcord"
# session="01" # TODO change if multiple sessions
# #average
# export analysis_path subject session run func_data region smoothing
# envsubst < "${PATH_SCRIPTS}/first_level_average.fsf" > "${subject}_${region}_first_level_average.fsf"
# feat ${subject}_${region}_first_level_average.fsf

# #trialwise average
# export analysis_path subject session run func_data region smoothing
# envsubst < "${PATH_SCRIPTS}/second_level_trialwise_average.fsf" > "${subject}_${region}_second_level_trialwise_average.fsf"
# feat ${subject}_${region}_second_level_trialwise_average.fsf



# Verify presence of output files and write log file if error
# ------------------------------------------------------------------------------
FILES_TO_CHECK=(
  "run-leftpinky/${file}_task-tens_run-leftpinky_bold_mc2_pnm_stc2template_smooth225.nii.gz"
  "run-rightpinky/${file}_task-tens_run-rightpinky_bold_mc2_pnm_stc2template_smooth225.nii.gz"
  "run-rightmiddle/${file}_task-tens_run-rightmiddle_bold_mc2_pnm_stc2template_smooth225.nii.gz"
  "run-leftmiddle/${file}_task-tens_run-leftmiddle_bold_mc2_pnm_stc2template_smooth225.nii.gz"
  "run-leftthumb/${file}_task-tens_run-leftthumb_bold_mc2_pnm_stc2template_smooth225.nii.gz"
  "run-rightthumb/${file}_task-tens_run-rightthumb_bold_mc2_pnm_stc2template_smooth225.nii.gz"
)


for file in ${FILES_TO_CHECK[@]}; do
  if [[ ! -e $file ]]; then
    echo "${SUBJECT}/func/${file} does not exist" >> $PATH_LOG/_error_check_output_files.log
  fi
done

# Display useful info for the log
end=`date +%s`
runtime=$((end-start))
echo
echo "~~~"
echo "SCT version: `sct_version`"
echo "Ran on:      `uname -nsr`"
echo "Duration:    $(($runtime / 3600))hrs $((($runtime / 60) % 60))min $(($runtime % 60))sec"
echo "~~~"
