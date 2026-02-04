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
bash convert_dcm2bids.sh -f ~/nilab/Dermatomal_Mapping_R01/Aim2/data/raw/sub-DMAim2HC001/ -s sub-DMAim2HC001 -x 01 -o ~/nilab/Dermatomal_Mapping_R01/Aim2/data/raw/sub-DMAim2HC001/
~~~
