"""
Spinal Cord Resting-State ICA using nilearn CanICA
====================================================
Applies group-level ICA to resting-state spinal cord fMRI data
already registered to the PAM50 template space.

Inputs expected
---------------
- Preprocessed 4D NIfTI files in PAM50 space (one per subject)
- (Optional) a PAM50 spinal cord mask to restrict decomposition

Usage
-----
    python spinal_cord_ica.py

Edit the CONFIG section below to match your dataset.
"""

import glob
import os
import warnings

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from nilearn import image, plotting
from nilearn.decomposition import CanICA

warnings.filterwarnings("ignore")


# ============================================================
# CONFIG — edit these paths/parameters for your dataset
# ============================================================

# Glob pattern that matches all your preprocessed 4D subjects files
# e.g. "/data/fmri/sub-*/func/sub-*_task-rest_space-PAM50_bold.nii.gz"
INPUT_DIR = "/home/sbedard/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/"
# sub-DMAim2HC001_ses-spinalcord_task-rest_bold_mc2_pnm_stc2template_smooth225.nii.gz
FUNC_PATTERN = f"{INPUT_DIR}/preprocessing_ALL/sub-*/ses-spinalcord/func/run-rest/sub-*_task-rest_bold_mc2_pnm_stc2template_smooth225.nii.gz"

# PAM50 spinal cord mask (strongly recommended — restricts ICA to cord voxels)
# Set to None to skip masking (not recommended for spinal cord data)
MASK_IMG = f"{INPUT_DIR}/masks/mask_n25.nii.gz"
# PAM50 template for reference
PAM50_T2 = f"/{INPUT_DIR}/masks/PAM50_t2_crop.nii.gz"

# Output directory

# ---- ICA parameters ----
N_COMPONENTS = 6        # Number of ICA components to extract
SMOOTHING_FWHM = None    # Spatial smoothing in mm (None = skip; cord data is often unsmoothed)
T_R =  2.5               # Repetition time in seconds — adjust to your acquisition
RANDOM_STATE = 42        # For reproducibility
N_JOBS = -1              # Parallel jobs (-1 = all available cores)

OUT_DIR = f"/home/sbedard/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/ica_results_{N_COMPONENTS}"

# Threshold for component maps when saving/plotting (z-score)
Z_THRESHOLD = 0

# ============================================================


def load_subject_imgs(pattern: str) -> list[str]:
    """Glob for subject functional images and validate."""
    imgs = sorted(glob.glob(pattern))
    if not imgs:
        raise FileNotFoundError(
            f"No files found matching pattern:\n  {pattern}\n"
            "Edit FUNC_PATTERN in the CONFIG section."
        )
    print(f"Found {len(imgs)} subject image(s):")
    for p in imgs:
        print(f"  {p}")
    return imgs


from nilearn.image import math_img

def zscore_components(components_img: nib.Nifti1Image) -> nib.Nifti1Image:
    """Z-score each component map across voxels."""
    data = components_img.get_fdata()  # (x, y, z, n_comp)
    
    mean = data.mean(axis=(0, 1, 2), keepdims=True)
    std  = data.std(axis=(0, 1, 2), keepdims=True)
    std[std == 0] = 1  # avoid division by zero in empty voxels
    
    zscored = (data - mean) / std
    return nib.Nifti1Image(zscored, components_img.affine, components_img.header)


def run_canica(
    imgs: list[str],
    mask_img,
    n_components: int,
    smoothing_fwhm,
    t_r: float,
    random_state: int,
    n_jobs: int,
) -> CanICA:
    """Fit CanICA on the group of functional images."""
    print(f"\nFitting CanICA with {n_components} components …")

    canica = CanICA(
        n_components=n_components,
        mask=mask_img,
        smoothing_fwhm=smoothing_fwhm,
        t_r=t_r,
        # Canonical ICA settings
        threshold=1.6,          # Threshold for brain masking (z-score)
        verbose=1,
        random_state=random_state,
        n_jobs=n_jobs,
        detrend=True,
        standardize=False,
        # Memory caching (speeds up re-runs)
        memory="nilearn_cache",
        memory_level=2,
    )
    canica.ica_params = {"max_iter": 500} 
    canica.fit(imgs)
    #canica.components_img_ = zscore_components(canica.components_img_)  # replace in-place
    print("CanICA fitting complete.")
    return canica


def save_components(canica: CanICA, out_dir: str) -> nib.Nifti1Image:
    """
    Extract and save:
      - 4D NIfTI with all component maps
      - Individual 3D NIfTIs per component
    Returns the 4D components image.
    """
    os.makedirs(out_dir, exist_ok=True)

    components_img = canica.components_img_
    n_components = components_img.shape[-1]

    # Save 4D image
    out_4d = os.path.join(out_dir, f"ica_components_4D_{n_components}.nii.gz")
    nib.save(components_img, out_4d)
    print(f"\nSaved 4D component image → {out_4d}")

    # Save individual components
    comp_dir = os.path.join(out_dir, "components")
    os.makedirs(comp_dir, exist_ok=True)
    for i in range(n_components):
        vol = image.index_img(components_img, i)
        fname = os.path.join(comp_dir, f"component_{i+1:02d}.nii.gz")
        nib.save(vol, fname)

    print(f"Saved {n_components} individual component maps → {comp_dir}/")
    return components_img


def plot_components(
    components_img: nib.Nifti1Image,
    out_dir: str,
    threshold: float,
):
    """
    Plot each ICA component as an axial mosaic and save to PNG.
    Uses stat_map display — useful for the elongated spinal cord FOV.
    """
    plot_dir = os.path.join(out_dir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    n_components = components_img.shape[-1]
    print(f"\nPlotting {n_components} components (threshold z={threshold}) …")

    for i in range(n_components):
        comp = image.index_img(components_img, i)

        # Stat map plot — coronal view works well for cord (superior→inferior axis)
        fig, axes = plt.subplots(1, 1, figsize=(12, 4))
        display = plotting.plot_stat_map(
            comp,
            display_mode="y",        # coronal slices along the cord
            cut_coords=8,
            bg_img=PAM50_T2,
            colorbar=True,
            threshold=threshold,
            title=f"ICA Component {i+1}",
            figure=fig,
            axes=axes,
            draw_cross=False,
        )
        out_png = os.path.join(plot_dir, f"component_{i+1:02d}.png")
        fig.savefig(out_png, dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"Plots saved → {plot_dir}/")


def main():
    # 1. Collect images
    imgs = load_subject_imgs(FUNC_PATTERN)

    # 2. Optional mask
    mask = MASK_IMG if (MASK_IMG and os.path.exists(MASK_IMG)) else None
    if MASK_IMG and mask is None:
        print(f"Warning: mask not found at {MASK_IMG} — running without mask.")

    # 3. Fit ICA
    canica = run_canica(
        imgs=imgs,
        mask_img=mask,
        n_components=N_COMPONENTS,
        smoothing_fwhm=SMOOTHING_FWHM,
        t_r=T_R,
        random_state=RANDOM_STATE,
        n_jobs=N_JOBS,
    )

    # 4. Save component maps
    components_img = save_components(canica, OUT_DIR)

    # 5. Plot components
    plot_components(components_img, OUT_DIR, threshold=Z_THRESHOLD)

    print(f"\nAll done. Results in: {os.path.abspath(OUT_DIR)}")


if __name__ == "__main__":
    main()