#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Creates plot per subject tsnr for each finger
# Example command: python plot_tsnr.py --data-dir ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/preprocessing_ALL/results/tsnr_maps_n25/ --mask ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/masks/mask_n25_PAM50.nii.gz --output ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/preprocessing_ALL/results/tsnr_maps_n25/figures_n25_tsnr.png
#!/usr/bin/env python3
"""
plot_tsnr_violin.py

Compute mean tSNR (within a mask) per subject/run from NIfTI tSNR maps,
and produce a violin+dots plot for each run.

ASSUMPTIONS (edit the constants below / pass CLI args to match your data):
  - One tSNR NIfTI file per subject per run, named following a glob-style
    pattern with {subject} and {run} placeholders, e.g.:
        sub-{subject}/sub-{subject}_task-{run}_tsnr.nii.gz
  - Either:
        (a) a single group-level mask applied to every subject, or
        (b) a per-subject mask following a pattern with {subject}.
  - tSNR value used per subject/run = mean of all voxels where mask > 0.

USAGE EXAMPLES
---------------
# Single group mask for everyone
python plot_tsnr_violin.py \
    --data-dir /path/to/data \
    --tsnr-pattern "sub-{subject}/sub-{subject}_task-{run}_tsnr.nii.gz" \
    --mask /path/to/data/group_mask.nii.gz \
    --output tsnr_violin.png

# Per-subject mask
python plot_tsnr_violin.py \
    --data-dir /path/to/data \
    --tsnr-pattern "sub-{subject}/sub-{subject}_task-{run}_tsnr.nii.gz" \
    --mask-pattern "sub-{subject}/sub-{subject}_mask.nii.gz" \
    --output tsnr_violin.png

# Restrict to specific subjects
python plot_tsnr_violin.py --data-dir /path/to/data --mask group_mask.nii.gz \
    --subjects 01 02 03 04
"""

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

try:
    import nibabel as nib
except ImportError:
    sys.exit("This script requires nibabel: pip install nibabel")

import matplotlib.pyplot as plt
import seaborn as sns


# The six runs to plot, in the order you want them to appear on the x-axis.
RUNS = [
    "rightthumb",
    "leftthumb",
    "rightmiddle",
    "leftmiddle",
    "rightpinky",
    "leftpinky",
]


def find_subjects(data_dir, tsnr_pattern, runs):
    """Auto-detect subject IDs by scanning for files matching the pattern
    with a wildcard in place of {subject}, using the first run as a probe."""
    probe_glob = os.path.join(
        data_dir, tsnr_pattern.format(subject="*", run=runs[0])
    )
    matches = sorted(glob.glob(probe_glob))
    subjects = []
    # Recover the {subject} value by matching against the non-wildcard parts
    prefix, suffix = tsnr_pattern.format(subject="\0", run=runs[0]).split("\0")
    prefix = os.path.join(data_dir, prefix)
    for m in matches:
        if m.startswith(prefix) and m.endswith(suffix):
            subj = m[len(prefix): len(m) - len(suffix)]
            subjects.append(subj)
    return subjects


def load_mask(mask_path):
    img = nib.load(mask_path)
    data = img.get_fdata()
    return data > 0


def mean_in_mask(nifti_path, mask_bool):
    img = nib.load(nifti_path)
    data = img.get_fdata()
    if data.shape != mask_bool.shape:
        raise ValueError(
            f"Shape mismatch: {nifti_path} has shape {data.shape}, "
            f"mask has shape {mask_bool.shape}"
        )
    values = data[mask_bool]
    values = values[np.isfinite(values)]  # drop NaN/Inf voxels
    if values.size == 0:
        return np.nan
    return float(np.mean(values))


def build_dataframe(data_dir, tsnr_pattern, subjects, runs,
                     mask_bool=None, mask_pattern=None):
    rows = []
    for subj in subjects:
        # Resolve the mask for this subject
        if mask_bool is not None:
            subj_mask = mask_bool
        else:
            mask_path = os.path.join(data_dir, mask_pattern.format(subject=subj))
            if not os.path.exists(mask_path):
                print(f"  [skip] no mask for subject {subj}: {mask_path}")
                continue
            subj_mask = load_mask(mask_path)

        for run in runs:
            tsnr_path = os.path.join(
                data_dir, tsnr_pattern.format(subject=subj, run=run)
            )
            if not os.path.exists(tsnr_path):
                print(f"  [missing] {tsnr_path}")
                continue
            try:
                val = mean_in_mask(tsnr_path, subj_mask)
            except ValueError as e:
                print(f"  [error] {e}")
                continue
            rows.append({"subject": subj, "run": run, "tsnr": val})

    return pd.DataFrame(rows)


def plot_violin(df, runs, output_path, title="Mean tSNR by run"):
    df = df.dropna(subset=["tsnr"]).copy()
    df["run"] = pd.Categorical(df["run"], categories=runs, ordered=True)
    df = df.sort_values("run")
 
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6.5))
 
    sns.violinplot(
        data=df, x="run", y="tsnr", order=runs,
        inner="box", color="#e6e6e6", linewidth=1, ax=ax, zorder=1
    )
 
    # One consistent color per subject
    subjects = sorted(df["subject"].unique())
    n_subj = len(subjects)
    palette = sns.color_palette("husl", n_subj)
    color_map = dict(zip(subjects, palette))
 
    # Fixed x-position per run, with a small deterministic per-subject
    # horizontal offset so lines don't overlap but still track cleanly
    run_x = {run: i for i, run in enumerate(runs)}
    if n_subj > 1:
        offsets = np.linspace(-0.18, 0.18, n_subj)
    else:
        offsets = np.array([0.0])
    offset_map = dict(zip(subjects, offsets))
 
    for subj in subjects:
        sub_df = df[df["subject"] == subj].copy()
        sub_df = sub_df.set_index("run").reindex(runs).dropna(subset=["tsnr"])
        if sub_df.empty:
            continue
        xs = [run_x[r] + offset_map[subj] for r in sub_df.index]
        ys = sub_df["tsnr"].values
        color = color_map[subj]
 
        ax.plot(xs, ys, color=color, alpha=0.6, linewidth=1.3, zorder=2)
        ax.scatter(xs, ys, color=color, s=45, edgecolor="white",
                   linewidth=0.5, zorder=3, label=subj)
 
    ax.set_xticks(range(len(runs)))
    ax.set_xticklabels(runs)
    ax.set_xlabel("Run")
    ax.set_ylabel("Mean tSNR (within mask)")
    ax.set_title(title)
    plt.xticks(rotation=20, ha="right")
 
    # Legend of subjects, placed outside the plot area
    ax.legend(
        title="Subject", bbox_to_anchor=(1.02, 1), loc="upper left",
        borderaxespad=0, fontsize=8, title_fontsize=9, ncol=1
    )
 
    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    print(f"Saved plot to {output_path}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", required=True, help="Root directory containing subject data")
    p.add_argument("--tsnr-pattern", default="sub-{subject}_ses-spinalcord_task-tens_run-{run}_bold_mc2_tsnr.nii.gz",
                   help="Path pattern (relative to --data-dir) with {subject} and {run} placeholders")
    p.add_argument("--mask", default=None, help="Single group-level mask NIfTI used for all subjects")
    p.add_argument("--mask-pattern", default=None,
                   help="Per-subject mask path pattern (relative to --data-dir) with {subject} placeholder. "
                        "Use this OR --mask, not both.")
    p.add_argument("--subjects", nargs="*", default=None,
                   help="Explicit list of subject IDs (e.g. 01 02 03). If omitted, auto-detected.")
    p.add_argument("--runs", nargs="*", default=RUNS,
                   help="Run names / order for the plot")
    p.add_argument("--output", default="tsnr_violin.png", help="Output image path")
    p.add_argument("--csv-output", default=None,
                   help="Optional path to also save the computed values as CSV")
    args = p.parse_args()

    if not args.mask and not args.mask_pattern:
        sys.exit("You must provide either --mask (single group mask) or --mask-pattern (per-subject).")
    if args.mask and args.mask_pattern:
        sys.exit("Provide only one of --mask or --mask-pattern, not both.")

    subjects = args.subjects
    if not subjects:
        print("No --subjects given, auto-detecting from tSNR pattern...")
        subjects = find_subjects(args.data_dir, args.tsnr_pattern, args.runs)
        print(f"Found subjects: {subjects}")
        if not subjects:
            sys.exit("No subjects found. Check --data-dir and --tsnr-pattern.")

    mask_bool = load_mask(args.mask) if args.mask else None

    print("Computing mean tSNR per subject/run...")
    df = build_dataframe(
        args.data_dir, args.tsnr_pattern, subjects, args.runs,
        mask_bool=mask_bool, mask_pattern=args.mask_pattern,
    )

    if df.empty:
        sys.exit("No tSNR values were computed — check your paths/patterns.")

    print(df.pivot(index="subject", columns="run", values="tsnr"))

    if args.csv_output:
        df.to_csv(args.csv_output, index=False)
        print(f"Saved values to {args.csv_output}")

    plot_violin(df, args.runs, args.output)


if __name__ == "__main__":
    main()