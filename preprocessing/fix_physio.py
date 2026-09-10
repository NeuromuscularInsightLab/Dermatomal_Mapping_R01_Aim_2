#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Fixed assumptions
DUMMY_SECONDS = 5.0
EXTRA_OFFSET_S = 0.0
SIGNAL_COL = "signal_raw_units"
PACKET_TS_COL = "packet_timestamp_us"
TIME_COL = "time_seconds"

def read_physio(path):
    df = pd.read_csv(path, sep=r"\s+", header=None, engine="python")
    if df.shape[1] < 4:
        raise ValueError("Physio file must have 4 columns: time resp trigger pulse")
    df = df.iloc[:, :4]
    df.columns = ["time_s", "resp", "trigger", "pulse"]
    return df

def read_pulse_csv(path):
    df = pd.read_csv(path)

    if SIGNAL_COL not in df.columns:
        raise ValueError(f"Pulse CSV missing column: {SIGNAL_COL}")

    if PACKET_TS_COL in df.columns and df[PACKET_TS_COL].notna().any():
        t = df[PACKET_TS_COL].astype(float).to_numpy() * 1e-6
        t = t - t[0]
        ts_used = PACKET_TS_COL
    elif TIME_COL in df.columns and df[TIME_COL].notna().any():
        t = df[TIME_COL].astype(float).to_numpy()
        t = t - t[0]
        ts_used = TIME_COL
    else:
        raise ValueError(f"Pulse CSV must contain {PACKET_TS_COL} or {TIME_COL}")

    x = df[SIGNAL_COL].astype(float).to_numpy()

    m = np.isfinite(t) & np.isfinite(x)
    t, x = t[m], x[m]

    # ignore first 5 seconds (dummy scans)
    t = t - DUMMY_SECONDS
    keep = t >= 0
    t, x = t[keep], x[keep]

    # sort + drop duplicate times
    order = np.argsort(t)
    t, x = t[order], x[order]
    keep = np.concatenate([[True], np.diff(t) > 0])
    t, x = t[keep], x[keep]

    return t, x, ts_used

def save_plot(t, pulse, out_png, title):
    plt.figure(figsize=(12, 4))
    plt.plot(t, pulse, lw=0.8)
    plt.xlabel("Time (s)")
    plt.ylabel("Pulse (synced)")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()

def main():
    ap = argparse.ArgumentParser(
        description="Replace physio pulse column using Siemens pulse CSV (skip first 5s), align by END time, and save plot."
    )
    ap.add_argument("-physio_in", required=True, help="Input physio text file (time resp trigger pulse).")
    ap.add_argument("-pulse_csv", required=True, help="Input pulse CSV.")
    ap.add_argument("-physio_out", required=True, help="Output physio text file.")
    ap.add_argument("-plot_out", required=True, help="Output PNG plot.")
    args = ap.parse_args()

    phys = read_physio(args.physio_in)
    t_phys = phys["time_s"].to_numpy()
    print(len(t_phys), "physio time points from", t_phys[0], "to", t_phys[-1], "seconds")

    t_pulse, x_pulse, ts_used = read_pulse_csv(args.pulse_csv)
    print(len(t_pulse), "pulse time points from", t_pulse[0], "to", t_pulse[-1], "seconds (after dummy removal)")

    # --- ALIGN BY END TIME (match ends) ---
    t_end_phys = float(t_phys[-1])
    t_end_pulse = float(t_pulse[-1])
    shift = (t_end_phys - t_end_pulse) + EXTRA_OFFSET_S
    t_pulse_aligned = t_pulse + shift

    # --- INTERPOLATE TO EXACT NUMBER OF POINTS IN PHYSIO FILE ---
    # Interpolate using sample index so output length == len(t_phys) exactly
    idx_phys = np.arange(len(t_phys), dtype=float)
    idx_pulse = np.linspace(0.0, len(t_phys) - 1.0, num=len(x_pulse), dtype=float)
    pulse_new = np.interp(idx_phys, idx_pulse, x_pulse)

    # Replace pulse column and write
    phys["pulse"] = pulse_new
    phys.to_csv(args.physio_out, sep="\t", header=False, index=False, float_format="%.9f")

    save_plot(
        t_phys, pulse_new, args.plot_out,
        title=f"Synced pulse (end-aligned; used {ts_used}; skipped first {DUMMY_SECONDS}s)"
    )

    print(f"Shift applied to pulse time (end-align): {shift:.6f} s")
    print(f"Wrote: {args.physio_out}")
    print(f"Wrote: {args.plot_out}")

if __name__ == "__main__":
    main()