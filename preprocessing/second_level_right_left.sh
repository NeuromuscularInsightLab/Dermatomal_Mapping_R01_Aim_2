data_path=/home/sbedard/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/preprocessing_ALL/
output_path=${data_path}/results/subject_level_right_left_2
scripts_path=/home/sbedard/codes/Dermatomal_Mapping_R01_Aim_2/preprocessing
task=tens
subjects=(sub-DMAim2HC001 sub-DMAim2HC002 sub-DMAim2HC003 sub-DMAim2HC004 sub-DMAim2HC013 sub-DMAim2HC009 sub-DMAim2HC012 sub-DMAim2HC020 sub-DMAim2HC011 sub-DMAim2HC005 sub-DMAim2HC016 sub-DMAim2HC021 sub-DMAim2HC018 sub-DMAim2HC023 sub-DMAim2HC014 sub-DMAim2HC025 sub-DMAim2HC017 sub-DMAim2HC019 sub-DMAim2HC027 sub-DMAim2HC026 sub-DMAim2HC006 sub-DMAim2HC041 sub-DMAim2HC044 sub-DMAim2HC038 sub-DMAim2HC029 sub-DMAim2HC030 sub-DMAim2HC034 sub-DMAim2HC057 sub-DMAim2HC039 sub-DMAim2HC054 sub-DMAim2HC042 sub-DMAim2HC046 sub-DMAim2HC032 sub-DMAim2HC043 sub-DMAim2HC056 sub-DMAim2HC040 sub-DMAim2HC059 sub-DMAim2HC060 sub-DMAim2HC050 sub-DMAim2HC051)
session=spinalcord

mkdir -p ${output_path}
tr=2.5

for subject in ${subjects[@]}; do

        cd ${output_path}
        analysis_path=$output_path
        smoothing=0
        export FSLDIR output_path scripts_path subject task analysis_path smoothing data_path tr
        envsubst < ${scripts_path}/design_subject_right_left.fsf > design_subject_right_left_${subject}.fsf
        feat design_subject_right_left_${subject}.fsf

    done