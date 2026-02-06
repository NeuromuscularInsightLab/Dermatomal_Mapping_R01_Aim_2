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

mkdir -p ${output_path}/ses-spinalcord${session}
mkdir -p ${output_path}/ses-spinalcord${session}/anat
#mkdir -p ${output_path}/ses-spinalcord${session}/dwi
mkdir -p ${output_path}/ses-spinalcord${session}/func
#mkdir -p ${output_path}/ses-spinalcord${session}/fmap


path_script=`pwd`
cd ${folder}
data_path=`pwd`

# Copy data to home directory for analysis
temp_folder=${subject}_temp`date +%Y%m%d%H%M%S`
#temp_folder=sub-DMAim2HC001_temp20260206124813
analysis_path=${HOME}/${temp_folder} #/${folder}
echo ${analysis_path}
mkdir -p ${analysis_path}

rsync -avz --exclude="*.dat" "${data_path}" "${analysis_path}/"

#Convert anat files
cd ${analysis_path}
exec > "${analysis_path}/dcm2niix.log" 2>&1
echo ${analysis_path}

if [ -d ${analysis_path} ]; then
  cd ${analysis_path}
  echo Converting ${analysis_path} to NIFTI
  dir=imaging
  #cd ./${dir}
  rm -rf ./nii_${dir}
  mkdir -p ./nii_${dir}
  echo Converting ${dir} to NIFTI
  dcm2niix -b y  -f %s -z y -x n -v y -o ./nii_${dir} ./*/${dir}

else
  echo Skipping ${analysis_path}/. Folder does not exist.
fi

#cd ${analysis_path}
# Find physiological log files (assuming they have "physio_log" in their name and end with .puls and .resp)
file_pulse=$(find "${analysis_path}" -type f -name "*physio_log*.puls" | head -n 1)
file_resp=$(find "${analysis_path}" -type f -name "*physio_log*.resp" | head -n 1)
echo ${dir}
cd ${analysis_path}/nii_${dir}
echo ${analysis_path}/nii_${dir}

for file in *.json; do  
  echo ${file}
  filename=${file::-5}
  
  if [ -f ${filename}.json ]; then
    series=`grep 'SeriesDescription' ${filename}.json`
  else
    series="No *json file in ${dir}"   
  fi


  echo $series
      

  ###########################################################################################
  #T2w
  ###########################################################################################
  
  if [[ ${series} == *"T2w_whole-spine"* ]] && [[ ${series} != *"cs25"* ]] && [[ ${series} != *"COMP"* ]]; then
    echo ${series}
    # Get the ProtocolName
    protocol=`grep 'ProtocolName' ${filename}.json`
    echo ${protocol}
    # Extract the last value from the protocol string (assuming it's after the last colon or space)
    if echo "${protocol}" | grep -q '0'; then
      acq=cervical
    elif echo "${protocol}" | grep -q '1'; then
      acq=thoracic
    elif echo "${protocol}" | grep -q '2'; then
      acq=lumbar
    elif  echo "${protocol}" | grep -q '3'; then
      acq=saccral
    fi
    echo ${acq}
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_T2w.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_T2w.nii.gz
  
  elif [[ ${series} == *"T2w_whole-spine"* ]] && [[ ${series} != *"cs25"* ]] && [[ ${series} == *"COMP"* ]]; then
    acq=wholespine
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_T2w.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_T2w.nii.gz

  elif [[ ${series} == *"T2w_whole-spine"* ]] && [[ ${series} == *"cs25"* ]]; then
    echo ${series}
        protocol=`grep 'ProtocolName' ${filename}.json`
    echo ${protocol}
    # Extract the last value from the protocol string (assuming it's after the last colon or space)
    if echo "${protocol}" | grep -q '0'; then
      acq=cervical
    elif echo "${protocol}" | grep -q '1'; then
      acq=thoracic
    elif echo "${protocol}" | grep -q '2'; then
      acq=lumbar
    elif  echo "${protocol}" | grep -q '3'; then
      acq=saccral
    fi
    
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_rec-accel_T2w.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_rec-accel_T2w.nii.gz
  
  elif [[ ${series} == *"T2w_whole-spine"* ]] && [[ ${series} == *"cs25"* ]]&& [[ ${series} == *"COMP"* ]]; then
    acq=wholespine
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_T2w.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-${acq}_T2w.nii.gz


  elif [[ ${series} == *"T2w_clinical"* ]]; then
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-sag_T2w.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-sag_T2w.nii.gz
  
  ###########################################################################################
  ###########################################################################################
  #Brachial Plexus STIR
  ###########################################################################################
  
  elif [[ ${series} == *"Brachial_Plexus"* ]] && [[ ${series} = *"STIR"* ]]; then
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-STIR_T2w.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/anat/${subject}_ses-spinalcord${session}_acq-STIR_T2w.nii.gz

  ###########################################################################################
  #SC Functional Scans
  ###########################################################################################
  elif [[ ${series} == *"rest"* ]]; then
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/func/${subject}_ses-spinalcord${session}_task-rest_bold.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/func/${subject}_ses-spinalcord${session}_task-rest_bold.nii.gz
    python ${path_script}/create_FSL_physio_text_file_from_Siemens_file.py -TR 2.5 -number-of-volumes 134 -pulse ${file_pulse} -resp ${file_resp} -json ${filename}.json
    cp ${filename}.physio ${output_path}/ses-spinalcord${session}/func/${subject}_ses-spinalcord${session}_task-rest_physio.physio

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
    cp ${filename}.json ${output_path}/ses-spinalcord${session}/func/${subject}_ses-spinalcord${session}_task-tens_run-${run}_bold.json
    cp ${filename}.nii.gz ${output_path}/ses-spinalcord${session}/func/${subject}_ses-spinalcord${session}_task-tens_run-${run}_bold.nii.gz
    python ${path_script}/create_FSL_physio_text_file_from_Siemens_file.py -TR 2.5 -number-of-volumes 134 -pulse ${file_pulse} -resp ${file_resp} -json ${filename}.json
    cp ${filename}.physio ${output_path}/ses-spinalcord${session}/func/${subject}_ses-spinalcord${session}_task-tens_run-${run}_physio.physio
  else 
    echo Skipping ${series}
  fi

done


###########################################################################################
#copy acq files to get stim parameters
###########################################################################################
#base_path=$(basename "${output_path}")
label_path="$HOME/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/labels"
mkdir -p ${label_path}/${subject}/ses-spinalcord/biopac/

cp -r ${analysis_path}/${subject}/biopac/*.acq ${label_path}/${subject}/ses-spinalcord/biopac/

exit 0