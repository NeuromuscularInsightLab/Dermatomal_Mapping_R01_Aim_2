#!/bin/sh
# 
#
path_script=~/codes/Dermatomal_Mapping_R01_Aim_2/preprocessing
PATH_DATA=${SCRATCH}/dm-aim2/sourcedata
PATH_SEGMANUAL=${SCRATCH}/dm-aim2/derivatives/labels
output_path=${SCRATCH}/dm-aim2/preprocessing_ALL_rest
subjects=(sub-DMAim2HC001 sub-DMAim2HC002 sub-DMAim2HC003 sub-DMAim2HC004 sub-DMAim2HC013 sub-DMAim2HC009 sub-DMAim2HC012 sub-DMAim2HC020 sub-DMAim2HC011 sub-DMAim2HC005 sub-DMAim2HC016 sub-DMAim2HC021 sub-DMAim2HC018 sub-DMAim2HC023 sub-DMAim2HC014 sub-DMAim2HC025 sub-DMAim2HC017 sub-DMAim2HC019 sub-DMAim2HC027 sub-DMAim2HC026 sub-DMAim2HC006)
ses=ses-spinalcord
NORDIC="" #nordic
time_limit=17:00:00
memory=64000

mkdir -p ${output_path}
PATH_DATA_PROCESSED="${output_path}/data_processed"
PATH_RESULTS="${output_path}/results"
PATH_LOG="${output_path}/log"
PATH_QC="${output_path}/qc"
mkdir -p ${PATH_DATA_PROCESSED}
mkdir -p ${PATH_RESULTS}
mkdir -p ${PATH_LOG}
mkdir -p ${PATH_QC}

for subject in "${subjects[@]}"; do
    echo "Preprocessing data for subject: $subject"
    export subject path_script PATH_DATA SCRATCH output_path time_limit memory PATH_DATA PATH_DATA_PROCESSED PATH_RESULTS PATH_LOG PATH_QC ses PATH_SEGMANUAL NORDIC
    envsubst '${subject} ${path_script} ${PATH_DATA} ${SCRATCH} ${output_path} ${time_limit} ${memory} ${PATH_DATA} ${PATH_DATA_PROCESSED} ${PATH_RESULTS} ${PATH_LOG} ${PATH_QC} ${ses} ${NORDIC}' < ${path_script}/preprocess.sbatch > preprocess_${subject}.sbatch
    sbatch preprocess_${subject}.sbatch
    rm preprocess_${subject}.sbatch
    sleep 10s
done
