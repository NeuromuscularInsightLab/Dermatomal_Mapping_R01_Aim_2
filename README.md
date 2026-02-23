# Dermatomal_Mapping_Aim_2

## Table of content
* [1.Dependencies](#1dependencies)
* [2.Installation](#2installation-of-python-requirements)

## 1.Dependencies

* Python 3.9

## 2.Installation of python requirements

* Create python environment
~~~
conda create --name venv-dm python==3.9
~~~

* Activate environment
~~~
conda activate venv-dm
~~~

* Install requirements
~~~
pip install -r requirements.txt
~~~


## 3. Data Conversion

~~~
conda activate venv-dm
cd Dermatomal_Mapping_R01_Aim_2/preprocessing
bash convert_dcm2bids.sh -f ~/nilab/Dermatomal_Mapping_R01/Aim2/data/raw/sub-DMAim2HC001/ -s sub-DMAim2HC001 -o ~/nilab/Dermatomal_Mapping_R01/Aim2/data/raw/sub-DMAim2HC001/
~~~

### 3a. NORDIC
~~~
./NORDIC_run_single_file.sh   ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/sourcedata/sub-DMAim2HC001/ses-01spinalcord/func/sub-DMAim2HC001_ses-01spinalcord_task-tens_bold.nii.gz  ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/sourcedata/sub-DMAim2HC001/ses-01spinalcord/func/sub-DMAim2HC001_ses-01spinalcord_task-tens_bold.nii.gz  ~/nilab/Individual_Folders/merve/Dermatomal_Mapping_R01/code/aim2/DermatomalMapping_Aim2/preprocessing/utils
~~~

#### Requirements
- MATLAB available on your system (`matlab` on PATH)
- NORDIC code path: (example: ~/nilab/Individual_Folders/merve/Dermatomal_Mapping_R01/code/aim2/DermatomalMapping_Aim2/preprocessing/utils)
- These two files in the same folder:
  - `NORDIC_run_single_file.sh`
  - `NORDIC_run_single_file.m`


## 4.Peak detection

## 5.Preprocessing

To run with nordic denoising, add argument "-script-args nordic"

~~~
sct_run_batc
h -script preprocess_spinal_cord.sh -path-data ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS
/sourcedata/ -path-out ~/dm_aim2_preprocessing_test -path-segmanual ~/nilab/Dermatomal_Mappi
ng_R01/Aim2/data/BIDS/derivatives/labels -script-args nordic
~~~

Without Nordic:
~~~
sct_run_batc
h -script preprocess_spinal_cord.sh -path-data ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS
/sourcedata/ -path-out ~/dm_aim2_preprocessing_test -path-segmanual ~/nilab/Dermatomal_Mappi
ng_R01/Aim2/data/BIDS/derivatives/labels
~~~


