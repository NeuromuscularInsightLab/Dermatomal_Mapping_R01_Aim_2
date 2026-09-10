#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_FSL_physio_text_file_from_csv.py

Build an FSL-compatible physio text file (columns: time, resp, trigger, pulse)
from per-run pulse and respiration CSV log files (one pulse CSV + one resp CSV
per fMRI run).

This merges two existing scripts:
  - create_FSL_physio_text_file_from_Siemens_file.py
        -> output format, trigger-vector construction, diagnostic plot
  - fix_physio.py
        -> CSV parsing (signal_raw_units / packet_timestamp_us / time_seconds),
           dummy-scan trimming, and "align by end time" strategy

Because a CSV log (unlike the Siemens .puls/.resp/.json triplet) does not carry
the scanner's absolute clock time, each trace is end-aligned: its last sample
is assumed to correspond to the end of the last acquired volume. If your CSVs
DO carry an absolute/shared clock with the scanner, let me know and this can
be swapped for start-of-acquisition alignment instead (more accurate).

Expected CSV format (one file for pulse, one for resp, per run):
    - a "signal_raw_units" column      (the physiological trace)
    - a "packet_timestamp_us" column (preferred, microseconds), OR
      a "time_seconds" column         (seconds)

Usage
-----
python create_FSL_physio_text_file_from_csv.py \
    -pulse_csv sub01_run01_pulse.csv \
    -resp_csv  sub01_run01_resp.csv \
    -TR 2.0 \
    -number-of-volumes 200 \
    -number-of-dummy 2 \
    -physio_out sub01_run01.physio \
    -plot_out sub01_run01_physio.png

Authors: (adapted from Sandrine Bedard & Kenneth Weber's original scripts)
"""

import argparse
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ------------------ Fixed column-name assumptions (from fix_physio.py) ------------------
SIGNAL_COL = "signal_raw_units"
PACKET_TS_COL = "packet_timestamp_us"
TIME_COL = "time_seconds"
SAMPLING_STEP_S = 0.02  # 50 Hz, matches original FSL physio convention


def get_parser():
    parser = argparse.ArgumentParser(
        description="Create an FSL physio.txt file (time, resp, trigger, pulse) "
                    "from separate pulse and respiration CSV log files, one pair per run."
    )
    parser.add_argument('-pulse_csv', required=True, type=str,
                         help="CSV file with the pulse/cardiac trace for this run")
    parser.add_argument('-resp_csv', required=True, type=str,
                         help="CSV file with the respiration trace for this run")
    parser.add_argument('-TR', required=True, type=float,
                         help="TR in seconds for each volume (sampling period of volumes)")
    parser.add_argument('-number-of-volumes', required=True, type=int,
                         help="Total number of volumes collected (including dummy scans)")
    parser.add_argument('-number-of-dummy', required=False, type=int, default=0,
                         help="Number of dummy scans to exclude from the start (default: 0)")
    parser.add_argument('-dummy-seconds', required=False, type=float, default=5.0,
                         help="Seconds to trim off the start of each CSV recording before use "
                              "(default: 5.0, matches fix_physio.py)")
    parser.add_argument('-physio_out', required=True, type=str,
                         help="Output physio text file (e.g. sub01_run01.physio)")
    parser.add_argument('-plot_out', required=False, type=str, default=None,
                         help="Output PNG plot (default: <physio_out>_physio_plot.png)")
    parser.add_argument('-exclude-resp', action='store_true',
                         help="Zero out the respiration channel")
    parser.add_argument('-exclude-pulse', action='store_true',
                         help="Zero out the pulse channel")
    return parser


def read_signal_csv(path, dummy_seconds, exclude=False):
    """
    Read a pulse or resp CSV log and return (time_s, signal, ts_used):
      - time referenced to 0 at the first recorded sample
      - the first `dummy_seconds` seconds trimmed off
      - sorted, duplicate-time samples dropped
    Generalizes fix_physio.py's read_pulse_csv() to also work for resp CSVs.
    """
    df = pd.read_csv(path)

    if SIGNAL_COL not in df.columns:
        raise ValueError(f"{path}: missing required column '{SIGNAL_COL}'")

    if PACKET_TS_COL in df.columns and df[PACKET_TS_COL].notna().any():
        t = df[PACKET_TS_COL].astype(float).to_numpy() * 1e-6
        ts_used = PACKET_TS_COL
    elif TIME_COL in df.columns and df[TIME_COL].notna().any():
        t = df[TIME_COL].astype(float).to_numpy()
        ts_used = TIME_COL
    else:
        raise ValueError(f"{path}: must contain '{PACKET_TS_COL}' or '{TIME_COL}'")

    t = t - t[0]
    x = df[SIGNAL_COL].astype(float).to_numpy()

    m = np.isfinite(t) & np.isfinite(x)
    t, x = t[m], x[m]

    # ignore the dummy-scan period at the start of the recording
    t = t - dummy_seconds
    keep = t >= 0
    t, x = t[keep], x[keep]

    # sort + drop duplicate timestamps
    order = np.argsort(t)
    t, x = t[order], x[order]
    keep = np.concatenate([[True], np.diff(t) > 0])
    t, x = t[keep], x[keep]

    if exclude:
        x = np.zeros_like(x)

    return t, x, ts_used


def align_and_resample(t_src, x_src, time_vector):
    """
    End-align a physiological trace to the run's time vector (last sample of
    the CSV <-> last sample of the run), then resample onto that vector.
    Same alignment philosophy as fix_physio.py's "ALIGN BY END TIME".
    """
    shift = time_vector[-1] - t_src[-1]
    t_aligned = t_src + shift
    return np.interp(time_vector, t_aligned, x_src, left=x_src[0], right=x_src[-1])


def build_trigger_vector(time_vector, TR, number_of_volumes, number_of_dummies):
    """
    One trigger pulse per acquired (non-dummy) volume, starting at t = 0
    (0 s = start of the first real volume), width = 10% of TR.
    Matches create_FSL_physio_text_file_from_Siemens_file.py.
    """
    n_real_volumes = number_of_volumes - number_of_dummies
    trigger_starts = np.arange(0, TR * n_real_volumes, TR)
    trigger_vector = np.zeros_like(time_vector)
    trigger_width = TR * 0.1
    width_samples = max(1, int(round(trigger_width / SAMPLING_STEP_S)))

    for t_start in trigger_starts:
        idx = int(round((t_start - time_vector[0]) / SAMPLING_STEP_S))
        if 0 <= idx < len(trigger_vector):
            trigger_vector[idx:idx + width_samples] = 1

    return trigger_vector


def create_FSL_physio_text_file_from_csv(pulse_csv, resp_csv, TR, number_of_volumes,
                                          number_of_dummies, dummy_seconds,
                                          physio_out, plot_out=None,
                                          exclude_resp=False, exclude_pulse=False):
    """
    Converts per-run pulse and respiration CSV log files into an FSL-compatible
    .physio text file. Columns: Time | Resp | Trigger | Pulse. Sampling rate: 50 Hz.
    """
    n_real_volumes = number_of_volumes - number_of_dummies

    # 0 s = start of the first (non-dummy) volume; starts 1 TR earlier,
    # ends at the end of the last real volume.
    time_vector = np.arange(-TR, TR * n_real_volumes + SAMPLING_STEP_S, SAMPLING_STEP_S)

    # ------------------ Pulse ------------------
    pulse_ts_used = None
    if not exclude_pulse:
        t_pulse, x_pulse, pulse_ts_used = read_signal_csv(pulse_csv, dummy_seconds)
        pulse_vector = align_and_resample(t_pulse, x_pulse, time_vector)
    else:
        pulse_vector = np.zeros_like(time_vector)

    # ------------------ Resp ------------------
    resp_ts_used = None
    if not exclude_resp:
        t_resp, x_resp, resp_ts_used = read_signal_csv(resp_csv, dummy_seconds)
        resp_vector = align_and_resample(t_resp, x_resp, time_vector)
    else:
        resp_vector = np.zeros_like(time_vector)

    # ------------------ Trigger ------------------
    trigger_vector = build_trigger_vector(time_vector, TR, number_of_volumes, number_of_dummies)

    # ------------------ Save physio text file ------------------
    physio_data = np.column_stack((time_vector, resp_vector, trigger_vector, pulse_vector))
    np.savetxt(physio_out, physio_data, fmt='%.9f', delimiter='\t')
    print(f"Saved FSL physio file: {physio_out}")
    print(f"  {len(time_vector)} samples, {time_vector[0]:.3f} s to {time_vector[-1]:.3f} s")
    if pulse_ts_used:
        print(f"  pulse timestamp column used: {pulse_ts_used}")
    if resp_ts_used:
        print(f"  resp timestamp column used: {resp_ts_used}")

    # ------------------ Plot ------------------
    if plot_out is None:
        plot_out = os.path.splitext(physio_out)[0] + "_physio_plot.png"

    fig, axes = plt.subplots(3, 1, figsize=(18, 9), sharex=True)
    axes[0].plot(time_vector, resp_vector, linewidth=0.5)
    axes[0].set_title('Respiration Data')
    axes[1].plot(time_vector, pulse_vector, linewidth=0.5)
    axes[1].set_title('Pulse Data')
    axes[2].plot(time_vector, trigger_vector, linewidth=0.5)
    axes[2].set_title('Scanner Triggers')
    for ax in axes:
        ax.set_xlabel('Time (s), 0 s = start of first (non-dummy) volume')
        ax.set_ylabel('Amplitude')
    plt.tight_layout()
    plt.savefig(plot_out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved plot: {plot_out}")

    return time_vector, pulse_vector, trigger_vector, resp_vector


def main():
    parser = get_parser()
    args = parser.parse_args()

    create_FSL_physio_text_file_from_csv(
        pulse_csv=args.pulse_csv,
        resp_csv=args.resp_csv,
        TR=args.TR,
        number_of_volumes=args.number_of_volumes,
        number_of_dummies=args.number_of_dummy,
        dummy_seconds=args.dummy_seconds,
        physio_out=args.physio_out,
        plot_out=args.plot_out,
        exclude_resp=args.exclude_resp,
        exclude_pulse=args.exclude_pulse,
    )


if __name__ == '__main__':
    main()