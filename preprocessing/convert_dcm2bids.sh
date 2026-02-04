#!/bin/bash
# 
#
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

function usage()
{
cat << EOF

DESCRIPTION
  Convert dcm to bids format for Dermatomal Mapping R01
  Requires that dcm2niix and FSL are installed.
  Requires fix_pixdim_and_affine.sh
  
USAGE
  `basename ${0}` -f <folder> -s <subject>

MANDATORY ARGUMENTS
  -f <folder>               Dicom folder from scanner (E#####)
  -s <subject>              Subject Study ID (sub-DMAim1HC###, or sub-DMAim2HC###, or sub-DMAim3HC###, or sub-DMAim3CR###)
  -x <session>              Optional argument to specify a session (Default=Blank)

EOF
}

if [ ! ${#@} -gt 0 ]; then
    usage `basename ${0}`
    exit 1
fi

#Initialization of variables

scriptname=${0}
folder=
subject=
session=
output_path=
while getopts “hf:s:x:o:” OPTION
do
  case $OPTION in
  h)
    usage
    exit 1
    ;;
  f)
    folder=$OPTARG
    ;;
  s)
    subject=$OPTARG
    ;;
  x)
    session=$OPTARG
    ;;
  o)
    output_path=$OPTARG
    ;;
  ?)
     usage
     exit
     ;;
  esac
done

script_path=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# # Check the parameters

if [[ -z ${folder} ]]; then
   echo "ERROR: Folder not specified. Exit program."
     exit 1
fi
if [[ -z ${subject} ]]; then
     echo "ERROR: Subject not specified. Exit program."
     exit 1
fi

#Setup output path
output_path=${output_path}/${subject}

mkdir -p ${output_path}

#mkdir -p ${output_path}/ses-brain21Ch${session}
#mkdir -p ${output_path}/ses-brain21Ch${session}/anat
#mkdir -p ${output_path}/ses-brain21Ch${session}/func
#mkdir -p ${output_path}/ses-brain21Ch${session}/fmap

#mkdir -p ${output_path}/ses-spinalcord21Ch${session}
#mkdir -p ${output_path}/ses-spinalcord21Ch${session}/anat
#mkdir -p ${output_path}/ses-spinalcord21Ch${session}/dwi
#mkdir -p ${output_path}/ses-spinalcord21Ch${session}/func
#mkdir -p ${output_path}/ses-spinalcord21Ch${session}/fmap

#mkdir -p ${output_path}/ses-brain56Ch${session}
#mkdir -p ${output_path}/ses-brain56Ch${session}/anat
#mkdir -p ${output_path}/ses-brain56Ch${session}/func
#mkdir -p ${output_path}/ses-brain56Ch${session}/fmap

#mkdir -p ${output_path}/ses-spinalcord56Ch${session}
#mkdir -p ${output_path}/ses-spinalcord56Ch${session}/anat
#mkdir -p ${output_path}/ses-spinalcord56Ch${session}/dwi
#mkdir -p ${output_path}/ses-spinalcord56Ch${session}/func
#mkdir -p ${output_path}/ses-spinalcord56Ch${session}/fmap

#mkdir -p ${output_path}/ses-brain${session}
#mkdir -p ${output_path}/ses-brain${session}/anat
#mkdir -p ${output_path}/ses-brain${session}/func
#mkdir -p ${output_path}/ses-brain${session}/fmap

mkdir -p ${output_path}/ses-spinalcord${session}
mkdir -p ${output_path}/ses-spinalcord${session}/anat
#mkdir -p ${output_path}/ses-spinalcord${session}/dwi
mkdir -p ${output_path}/ses-spinalcord${session}/func
#mkdir -p ${output_path}/ses-spinalcord${session}/fmap



cd ${folder}
data_path=`pwd`

# Copy data to home directory for analysis
temp_folder=${subject}_temp`date +%Y%m%d%H%M%S`
temp_folder=sub-DMAim2HC001_temp20260203134026
analysis_path=${HOME}/${temp_folder} #/${folder}
echo ${analysis_path}
mkdir -p ${analysis_path}

#rsync -avz --exclude="*.dat" --exclude="biopac/" "${data_path}" "${analysis_path}/"
#Convert anat files
cd ${analysis_path}
exec > "${analysis_path}/dcm2niix.log" 2>&1
echo ${analysis_path}

if [ -d ${analysis_path} ]; then
    cd ${analysis_path}
    echo Converting ${analysis_path} to NIFTI
    for dir in */ ; do
      echo Converting ${dir} to NIFTI
      rm -rf ./nii_${dir}
      mkdir ./nii_${dir}
      dcm2niix -b y  -f %s -z y -x n -v y -o ./nii_${dir} ./${dir}
    done
# elif [ -d ${analysis_path}/anat ]; then
#       cd ${analysis_path}/anat
#       echo Converting ${analysis_path}/anat to NIFTI
#       for dir in */ ; do
#         echo Converting ${dir} to NIFTI
#         rm -rf ../nii_${dir}
#         mkdir ../nii_${dir}
#         dcm2niix -b y  -f %s -z y -x n -v y -o ../nii_${dir} ./${dir}
#       done

else
  echo Skipping ${analysis_path}/. Folder does not exist.
fi

#Convert func files
# if [ -d ${analysis_path}/data ]; then
#   cd ${analysis_path}/data
#   echo Converting ${analysis_path}/data to NIFTI
#   echo ${analysis_path}
#   for dir in e${folder:1}*/ ; do
#     echo Converting ${dir} to NIFTI
#     rm -rf ../nii_${dir}
#     mkdir ../nii_${dir}
#     dcm2niix -b y -f %s -z y -x n -v y -o ../nii_${dir} ./${dir}/matlabDicoms
#   done
# elif [ -d ${analysis_path} ]; then
#   cd ${analysis_path}
#   echo Converting ${analysis_path} to NIFTI
#   echo ${analysis_path}
#   for dir in e${folder:1}*/ ; do
#     echo Converting ${dir} to NIFTI
#     rm -rf ../nii_${dir}
#     mkdir ../nii_${dir}
#     dcm2niix -b y -f %s -z y -x n -v y -o ../nii_${dir} ./${dir}/matlabDicoms
#   done
# else
#   echo Skipping ${analysis_path}/data or ${analysis_path}. Folder does not exist.
# fi

cd ${analysis_path}
file_pulse=$(find "${analysis_path}" -type f -name "*physio_log*.puls" | head -n 1)
file_resp=$(find "${analysis_path}" -type f -name "*physio_log*.resp" | head -n 1)
for dir in nii_*/ ; do
  echo ${dir}
  cd ${analysis_path}/${dir}
  echo ${analysis_path}/${dir}
  i=0
  j=0
  for file in *.json; do  
    echo ${file}
    filename=${file::-5}
    
    if [ -f ${filename}.json ]; then
     series=`grep 'SeriesDescription' ${filename}.json`
      if [[ ${series} == *"21-Ch"* ]]; then
        coil=21Ch
      elif [[ ${series} == *"56-Ch"* ]]; then
        coil=56Ch
      else
        coil=
      fi

    else
     series="No *json file in ${dir}"   
    fi

  
    echo $series
        
    ###########################################################################################
    #T1w
    ###########################################################################################
    if [[ ${series} == *"T1w"* ]] && [[ ${series} != *"ORIG"* ]] && [[ ${series} != *"GRE-T1w"* ]]; then

      cp ${filename}.json ${output_path}/ses-brain${coil}${session}/anat/${subject}_ses-brain${coil}${session}_T1w.json
      cp ${filename}.nii.gz ${output_path}/ses-brain${coil}${session}/anat/${subject}_ses-brain${coil}${session}_T1w.nii.gz

      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_T1w.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_T1w.nii.gz

    
    ###########################################################################################
    #T2w
    ###########################################################################################
    
    elif [[ ${series} == *"T2w_whole-spine"* ]] && [[ ${series} != *"cs25"* ]]; then
      echo ${series}
      if [[ $i -eq 0 ]]; then
        acq=cervical
      elif [[ $i -eq 1 ]]; then
        acq=thoracic
      elif [[ $i -eq 2 ]]; then
        acq=lumbar
      else
        acq=wholespine
      fi
      echo ${acq} $i
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-${acq}_T2w.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-${acq}_T2w.nii.gz
      i=$((i+1))
    
    elif [[ ${series} == *"T2w_whole-spine"* ]] && [[ ${series} == *"cs25"* ]]; then
      echo ${series}
      if [[ $j -eq 0 ]]; then
        acq=cervical
      elif [[ $j -eq 1 ]]; then
        acq=thoracic
      elif [[ $j -eq 2 ]]; then
        acq=lumbar
      else
        acq=wholespine
      fi      
      j=$((j+1))
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-${acq}_rec-accel_T2w.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-${acq}_rec-accel_T2w.nii.gz

      # TODO: fix for all chunks
      # Todo also for CS25
    elif [[ ${series} == *"T2w_clinical"* ]]; then
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-sag_T2w.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-sag_T2w.nii.gz
    ###########################################################################################
    ###########################################################################################
    #Brachial Plexus STIR
    ###########################################################################################
    
    elif [[ ${series} == *"Brachial_Plexus"* ]] && [[ ${series} = *"STIR"* ]]; then
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-STIR_T2w.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-STIR_T2w.nii.gz


    ###########################################################################################
    #Functional Scans
    ###########################################################################################

    ###########################################################################################
    #Brain Functional Scans
    ###########################################################################################

    # elif ([[ ${series} == *"run-1"* ]] || [[ ${series} == *"run-2"* ]] || [[ ${series} == *"run-3"* ]])  && [[ ${dir} != "nii_e"* ]] && [[ ${series} == *"brain"* ]]  && [[ ${series} != *"pepolar"* ]]; then

    #   if [[ ${series} == *"run-1"* ]]; then
    #     run=1
    #   elif [[ ${series} == *"run-2"* ]]; then
    #     run=2
    #   elif [[ ${series} == *"run-3"* ]]; then
    #     run=3
    #   else
    #     run=
    #   fi
      
    #   cp ${filename}.json ${output_path}/ses-brain${coil}${session}/func/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_bold.json
    #   cp ${filename}.nii.gz ${output_path}/ses-brain${coil}${session}/func/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_bold.nii.gz
      
    #   physio_file=`ls ${analysis_path}/*S$(printf "%03d" ${filename})P*`

    #   cp ${analysis_path}/${physio_file: -8:6}.physio ${output_path}/ses-brain${coil}${session}/func/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_physio.physio
    #   sed -i 's/"ConversionSoftwareVersion"/"PhaseEncodingDirection": "j",\n\t"ConversionSoftwareVersion"/' ${output_path}/ses-brain${coil}${session}/func/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_bold.json
    #   sed -i 's/"SAR"/"TaskName": "'"tens"'",\n\t"SAR"/' ${output_path}/ses-brain${coil}${session}/func/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_bold.json

    ###########################################################################################
    #Brain pepolar
    ###########################################################################################

    # elif ([[ ${series} == *"run-1_pepolar"* ]] || [[ ${series} == *"run-2_pepolar"* ]] || [[ ${series} == *"run-3_pepolar"* ]]) && [[ ${dir} != "nii_e"* ]] && [[ ${series} == *"brain"* ]] && [[ ${series} == *"pepolar"* ]]; then
      
    #   if [[ ${series} == *"run-1"* ]]; then
    #     run=1
    #   elif [[ ${series} == *"run-2"* ]]; then
    #     run=2
    #   elif [[ ${series} == *"run-3"* ]]; then
    #     run=3
    #   else
    #     run=
    #   fi
      
    #   cp ${filename}.json ${output_path}/ses-brain${coil}${session}/fmap/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_dir-AP_bold.json
    #   cp ${filename}.nii.gz ${output_path}/ses-brain${coil}${session}/fmap/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_dir-AP_bold.nii.gz

    #   sed -i 's/"ConversionSoftwareVersion"/"PhaseEncodingDirection": "j-",\n\t"ConversionSoftwareVersion"/' ${output_path}/ses-brain${coil}${session}/fmap/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_dir-AP_bold.json
    #   sed -i 's/"ConversionSoftwareVersion"/"IntendedFor": "ses-brain${coil}${session}\/func\/'${subject}'_ses-brain${coil}${session}_task-tens_run-${run}_bold.nii.gz",\n\t"ConversionSoftwareVersion"/' ${output_path}/ses-brain${coil}${session}/fmap/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_dir-AP_bold.json
    #   sed -i 's/"SAR"/"TaskName": "'"tens"'",\n\t"SAR"/' ${output_path}/ses-brain${coil}${session}/fmap/${subject}_ses-brain${coil}${session}_task-tens_run-${run}_dir-AP_bold.json
    
    ###########################################################################################
    #SC Functional Scans
    ###########################################################################################
    elif [[ ${series} == *"rest"* ]]; then
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-rest_bold.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-rest_bold.nii.gz
      python ~/codes/Dermatomal_Mapping_R01_Aim_2/preprocessing/create_FSL_physio_text_file_from_Siemens_file.py -TR 2.5 -number-of-volumes 134 -pulse ${file_pulse} -resp ${file_resp} -json ${filename}.json
      cp ${filename}.physio ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-rest_physio.physio

    elif ([[ ${series} == *"leftthumb"* ]] || [[ ${series} == *"rightthumb"* ]] || [[ ${series} == *"leftmiddle"* ]] || [[ ${series} == *"rightmiddle"* ]] || [[ ${series} == *"leftpinky"* ]] || [[ ${series} == *"rightpinky"* ]]); then

      if [[ ${series} == *"leftthumb"* ]]; then
        run=leftthumb
      elif [[ ${series} == *"rightthumb"* ]]; then
        run=rightthumb
      elif [[ ${series} == *"leftmiddle"* ]]; then
        run=leftmiddle
      elif [[ ${series} == *"rightmiddle"* ]]; then
        run=rightmiddle
      elif [[ ${series} == *"leftpinky"* ]]; then
        run=leftpinky
      elif [[ ${series} == *"rightpinky"* ]]; then
        run=rightpinky
      else
        run=
      fi

      # series_folder=`echo ${dir} | cut -d "_" -f2`
      # if [ -e "${analysis_path}/data/${series_folder}" ]; then
      #   recon_json_file="${analysis_path}/data/${series_folder}/*.json"
      # else
      #   recon_json_file="${analysis_path}/${series_folder}/*.json"
      # fi
      # pfile=`grep 'Pfile_name' ${recon_json_file} | cut -d ' ' -f3 | cut -d ',' -f1`
      # #Add leading zeros to pfile
      # pfile=$(printf "%05d" ${pfile})
      
      # calculate TotalReadoutTime 
      # if PartialFourer=1, TotalReadoutTime = EffectiveEchoSpacing * (rdb_hdr_rc_yres / ksepi_multishot_control / 2 + kynover / ksepi_multishot_control)
      # if PartialFourer=0, TotalReadoutTime = EffectiveEchoSpacing * rdb_hdr_rc_yres / ksepi_multishot_control 
      # EES=`grep 'EffectiveEchoSpacing' ${recon_json_file} | cut -f3 -d ' '`
      # Ny=`grep 'rdb_hdr_rc_yres' ${recon_json_file} | cut -f3 -d ' ' | cut -f1 -d ','`
      # R=`grep 'ksepi_multishot_control' ${recon_json_file} | cut -f3 -d ' ' | cut -f1 -d ','`
      # kynover=`grep 'kynover' ${recon_json_file} | cut -f3 -d ' ' | cut -f1 -d ','`
      # PartialFourier=0
      # if [[ ${PartialFourier} -eq 1 ]]; then
      #   TotalReadoutTime=`echo "$EES*$Ny/$R/2+$EES*$kynover/$R" | bc -l`
      # else
      #   TotalReadoutTime=`echo "$EES*$Ny/$R" | bc -l`
      # fi
      # echo "EES=$EES, Ny=$Ny, R=$R, kynover=$kynover, TotalReadoutTime=$TotalReadoutTime"
      
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-tens_run-${run}_bold.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-tens_run-${run}_bold.nii.gz

      python ~/codes/Dermatomal_Mapping_R01_Aim_2/preprocessing/create_FSL_physio_text_file_from_Siemens_file.py -TR 2.5 -number-of-volumes 134 -pulse ${file_pulse} -resp ${file_resp} -json ${filename}.json
      cp ${filename}.physio ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-tens_run-${run}_physio.physio
      # TODO: process physio file to split them per run

      #cp ${analysis_path}/P${pfile}.physio ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-tens_run-${run}_physio.physio
      # sed -i 's/"ConversionSoftwareVersion"/"PhaseEncodingDirection": "j",\n\t"ConversionSoftwareVersion"/' ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-tens_run-${run}_bold.json
      # sed -i 's/"SAR"/"TaskName": "'"tens"'",\n\t"SAR"/' ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-tens_run-${run}_bold.json
      # sed -i 's/"SAR"/"TotalReadoutTime": "'"${TotalReadoutTime}"'",\n\t"SAR"/' ${output_path}/ses-spinalcord${coil}${session}/func/${subject}_ses-spinalcord${coil}${session}_task-tens_run-${run}_bold.json

    ###########################################################################################
    #SC_DWI
    ###########################################################################################

    elif [[ ${series} == *"DWI"* ]]; then
        cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/dwi/${subject}_ses-spinalcord${coil}${session}_dwi.json
        cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/dwi/${subject}_ses-spinalcord${coil}${session}_dwi.nii.gz
        cp ${filename}.bval ${output_path}/ses-spinalcord${coil}${session}/dwi/${subject}_ses-spinalcord${coil}${session}_dwi.bval
        cp ${filename}.bvec ${output_path}/ses-spinalcord${coil}${session}/dwi/${subject}_ses-spinalcord${coil}${session}_dwi.bvec

    ###########################################################################################
    #MERGE
    ###########################################################################################

    elif [[ ${series} == *"MERGE"* ]] && [[ ${series} != *"ORIG"* ]]; then
        cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_T2star.json
        cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_T2star.nii.gz
    
    ###########################################################################################
    #MT
    ###########################################################################################

    elif [[ ${series} == *"GRE-T1w"* ]] && [[ ${series} != *"ORIG"* ]]; then
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-T1w_MTS.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-T1w_MTS.nii.gz

    elif [[ ${series} == *"GRE-MT1"* ]] && [[ ${series} != *"ORIG"* ]]; then
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-MTon_MTS.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-MTon_MTS.nii.gz

    elif [[ ${series} == *"GRE-MT0"* ]] && [[ ${series} != *"ORIG"* ]]; then
      cp ${filename}.json ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-MToff_MTS.json
      cp ${filename}.nii.gz ${output_path}/ses-spinalcord${coil}${session}/anat/${subject}_ses-spinalcord${coil}${session}_acq-MToff_MTS.nii.gz
    

    else 
      echo Skipping ${series}
    fi

  done

done

###########################################################################################
#copy fsl_stim_vectors
###########################################################################################
#base_path="${output_path%/*/*/*/*}"  # Removes the last three directories
#label_path="${base_path}/BIDS/derivatives/labels"
#mkdir ${label_path}/${subject}

#cp -r ${base_path}/raw/${subject}/biopac/fsl_stim_vectors ${label_path}/${subject}/
#TODO: 
cp 


exit 0