#!/usr/bin/env python
# -*- coding: utf-8
# Create FSL physio.txt file 
#
# For usage, type: python create_FSL_physio_text_file_from_Siemens_file.py -h

# File takes in the pfile.physio (fname) and then outputs text file for physiological noise correction with FSL
# Function was written and tested using FSL 5.0 and MATLAB R2015b. End of
# physiological data used as the end of the output physio file. Start of
# output file equals end - total time (TR * number_of_volumes). This way the
# physiological data from any dummy scans are not included in the output file.
# Based on https://gist.github.com/rtrhd/6172344
# Authors: Sandrine Bédard & Kenneth Weber

import argparse
import numpy as np
from math import floor
import matplotlib.pyplot as plt
import re
import json
from scipy.signal import decimate
from datetime import datetime
import os


def get_parser():
    parser = argparse.ArgumentParser(
        description="Plot physio data.")
    parser.add_argument('-pulse', required=True, type=str,
                        help="filename for pfile.physio")
    parser.add_argument('-resp', required=True, type=str,
                        help="filename for pfile.resp")
    parser.add_argument('-json', required=True, type=str,
                        help="filename for pfile.json")
    parser.add_argument('-TR', required=True, type=float,
                        help="TR in seconds for each volume (i.e., sampling period of volumes)")
    parser.add_argument('-number-of-volumes', required=True, type=int,
                        help="Number of volumes collected")
    parser.add_argument('-exclude-resp', action='store_true',
                        help="To put 0 values in respiratory data")
    return parser

def plot_data(cardiac_time_data, cardiac_data, respiration_data_interp, trigger_data):

    plt.figure()
    # Cardiac data
    ax = plt.subplot(311)
    ax.plot(cardiac_time_data, cardiac_data, linewidth=0.5)
    ax.set_title('Cardiac Data', fontsize=10)
    ax.tick_params(axis='both', which='major', labelsize=7)
    ax.set_xlabel('Time (s) with 0 s = start of first volume', fontsize=7)
    ax.set_ylabel('Amplitude', fontsize=7)
    ax.set_xlim(min(cardiac_time_data), max(cardiac_time_data))
    ax.set_ylim(min(cardiac_data)-(0.10*abs(min(cardiac_data))), max(cardiac_data)+(0.10*abs(max(cardiac_data))))

    # Respiration data
    ax1 = plt.subplot(312)
    ax1.plot(cardiac_time_data, respiration_data_interp, linewidth=0.5)
    ax1.tick_params(axis='both', which='major', labelsize=7)
    ax1.set_title('Respiration Data', fontsize=10)
    ax1.set_xlabel('Time (s) with 0 s = start of first volume', fontsize=7)
    ax1.set_ylabel('Amplitude', fontsize=7)
    ax1.set_xlim(min(cardiac_time_data), max(cardiac_time_data))
    ax1.set_ylim(min(respiration_data_interp)-(0.10*abs(min(respiration_data_interp))), max(respiration_data_interp)+(0.10*abs(max(respiration_data_interp))))

    # Trigger data
    ax2 = plt.subplot(313)
    ax2.plot(cardiac_time_data, trigger_data, linewidth=0.5)
    ax2.set_title('Scanner Triggers', fontsize=10)
    ax2.tick_params(axis='both', which='major', labelsize=7)
    ax2.set_xlabel('Time (s) with 0 s = start of first volume', fontsize=7)
    ax2.set_ylabel('Amplitude', fontsize=7)
    ax2.set_xlim(min(cardiac_time_data), max(cardiac_time_data))
    ax2.set_ylim(min(trigger_data)-(0.10*abs(min(trigger_data))), max(trigger_data)+(0.10*abs(max(trigger_data))))
    plt.tight_layout()
    plt.savefig('physio.png', dpi=600, bbox_inches="tight")


def create_FSL_physio_text_file_from_Siemens_file(pulse_fname, resp_fname, json_fname, TR, number_of_volumes):
    """
    Converts Siemens physiological log files to FSL-compatible .physio text file.
    Sampling rate = 50 Hz
    Columns: Time | Resp | Trigger | Pulse
    """

    # ------------------ Read Pulse data ------------------
    with open(pulse_fname, 'r') as f:
        pulse_data = f.read()
    f = None
    try:
        f = pulse_fname if hasattr(pulse_fname, 'read') else open(pulse_fname)
        lines = [line for line in f]
    finally:
        if f:
            f.close()
    fields = lines[0].split(' ')
    print(fields[:40])
    # find first occurrence of '6002' element in fields
    first_6002_index = fields.index('6002') if '6002' in fields else -1
    print(first_6002_index)

    pulse_trace = np.array(fields[first_6002_index + 1 :])[:-1]#.astype(float)  # remove last 5003 trigger

    #pulse_indices = [m.start() for m in re.finditer('6002', first_line)]
   # pulse_trace = np.fromstring(first_line[pulse_indices[0]:], sep=' ', dtype=int)


    pulse_start_time = int(re.search(r'LogStartMDHTime:\s+(\d+)', pulse_data).group(1))
    pulse_stop_time = int(re.search(r'LogStopMDHTime:\s+(\d+)', pulse_data).group(1))

    # Remove peak detection spikes (value == 5000)
    clean_fields = []
    include = True
    ninfos = 0
    debug = True
    for field in pulse_trace:  # TODO: why 8?
        if include:
            if field == '5002':
                include = False
                excluded = []
            else:
                clean_fields.append(field)
        else:
            if field == '6002':
                include = True
                if debug:
                    print("Excluded info field: '%s'" % ' '.join(excluded))
                    ninfos += 1
            else:
                excluded.append(field)

    pulse_trace = np.asarray([int(field) for field in clean_fields])
    spikes = np.where(pulse_trace == 5000)[0]
    for i in spikes:
        if 0 < i < len(pulse_trace) - 1:
            pulse_trace[i] = (pulse_trace[i - 1] + pulse_trace[i + 1]) / 2

    # Round start and stop times to nearest 20 ms (5 ms in ms units = 20 ms step)
    pulse_start_time = round(pulse_start_time / 20) * 20
    pulse_stop_time = round(pulse_stop_time / 20) * 20

    # Create pulse time vector and resample to 50 Hz (20 ms)
    pulse_time = np.arange(pulse_start_time, pulse_stop_time + 1, 20)
    print('length pulse time:', len(pulse_time), 'length pulse trace:', len(pulse_trace))
    pulse_trace = decimate(pulse_trace, 8)
    figure, ax = plt.subplots()
    ax.plot(pulse_trace)
    plt.savefig('pulse_trace_plot.png', dpi=300, bbox_inches="tight")
    plt.close(figure)
    # ------------------ Read Resp data ------------------
    with open(resp_fname, 'r') as f:
         resp_data = f.read()
    try:
        f = resp_fname if hasattr(resp_fname, 'read') else open(resp_fname)
        lines = [line for line in f]
    finally:
        if f:
            f.close()
    fields = lines[0].split(' ')
    print(fields[:40])
    # find 5th occurrence of '6002' element in fields
    # Find the 5th occurrence of '6002' in fields
    occurrences = [i for i, x in enumerate(fields) if x == '6002']
    fifth_6002_index = occurrences[4] if len(occurrences) >= 5 else -1
    resp_trace = np.array(fields[fifth_6002_index + 1 :])[:-1]  # remove last 5003 trigger

    resp_start_time = int(re.search(r'LogStartMDHTime:\s+(\d+)', resp_data).group(1))
    resp_stop_time = int(re.search(r'LogStopMDHTime:\s+(\d+)', resp_data).group(1))
    clean_fields = []
    include = True
    ninfos = 0
    debug = True
    for field in resp_trace:  # TODO: why 8?
        if include:
            if field == '5002':
                include = False
                excluded = []
            else:
                clean_fields.append(field)
        else:
            if field == '6002':
                include = True
                if debug:
                    #print("Excluded info field: '%s'" % ' '.join(excluded))
                    ninfos += 1
            else:
                excluded.append(field)

    resp_trace = np.asarray([int(field) for field in clean_fields])

    resp_trace = resp_trace.astype(float)
    spikes = np.where(resp_trace == 5000)[0]
    for i in spikes:
        if 0 < i < len(resp_trace) - 1:
            resp_trace[i] = (resp_trace[i - 1] + resp_trace[i + 1]) / 2

    # Round start and stop times to nearest 20 ms
    resp_start_time = round(resp_start_time / 20) * 20
    resp_stop_time = round(resp_stop_time / 20) * 20

    # Create resp time vector and resample to 50 Hz (20 ms)
    resp_time = np.arange(resp_start_time, resp_stop_time + 1, 20)
    resp_trace = decimate(resp_trace, 8)

    figure, ax = plt.subplots()
    ax.plot(resp_trace)
    plt.show()
    plt.close(figure)
    # ------------------ Read JSON data ------------------
    with open(json_fname, 'r') as f:
        json_data = json.load(f)
    try:
        acquisition_time_str = json_data["AcquisitionTime"]
    except KeyError:
        raise ValueError("AcquisitionTime not found in JSON file")
    print(acquisition_time_str)
    H, MN, S = map(float, acquisition_time_str.split(':'))
    acquisition_time = ((H * 3600) + (MN * 60) + S) * 1000
    acquisition_time = round(acquisition_time / 20) * 20
    print(f'Acquisition time (ms): {acquisition_time}')
    # ------------------ Create time vector ------------------
    time_vector = np.arange(acquisition_time - (TR * 1000),
                            acquisition_time + (TR * number_of_volumes * 1000) + 1,
                            20)
    #print(time_vector)
    # ------------------ Extract pulse and resp data ------------------
    def get_segment(trace, time, start, stop):
        start_idx = np.where(time == start)[0]
        stop_idx = np.where(time == stop)[0]
        #start_idx = np.argmin(np.abs(time - start))
        #stop_idx = np.argmin(np.abs(time - stop))
        print('Start idx:', start_idx, 'Stop idx:', stop_idx)
        print('Length of trace:', len(trace))
        if start_idx.size == 0 or stop_idx.size == 0:
            raise ValueError("Time indices not found in physiological data range.")
        return trace[start_idx[0]:stop_idx[0] + 1]

    pulse_vector = get_segment(pulse_trace, pulse_time,
                               acquisition_time - (TR * 1000),
                               acquisition_time + (TR * number_of_volumes * 1000))
    #print('Pulse vector', pulse_vector)
    resp_vector = get_segment(resp_trace, resp_time,
                              acquisition_time - (TR * 1000),
                              acquisition_time + (TR * number_of_volumes * 1000))
    #print('Resp vector', resp_vector)
    # ------------------ Create trigger vector ------------------
    trigger_starts = np.arange(acquisition_time,
                               acquisition_time + (TR * (number_of_volumes - 1) * 1000) + 1,
                               TR * 1000)
    trigger_vector = np.zeros_like(time_vector)
    trigger_width = TR * 0.1  # 10% of TR
    width_samples = int((trigger_width * 1000) / 20)

    for i, t_start in enumerate(trigger_starts):
        idx = np.where(time_vector == t_start)[0]
        if idx.size > 0:
            idx = idx[0]
            trigger_vector[idx:idx + width_samples] = 1

    # ------------------ Convert time to seconds (0 = start of run) ------------------
    time_vector = np.arange(-TR, TR * number_of_volumes + 0.02, 0.02)

    # ------------------ Plot results ------------------
    fig, axes = plt.subplots(3, 1, figsize=(18, 9), sharex=True)
    axes[0].plot(time_vector, resp_vector)
    axes[0].set_title('Resp Data')
    axes[1].plot(time_vector, pulse_vector)
    axes[1].set_title('Pulse Data')
    axes[2].plot(time_vector, trigger_vector)
    axes[2].set_title('Scanner Triggers')

    for ax in axes:
        ax.set_xlabel('Time (s) with 0 s = start of first volume')
        ax.set_ylabel('Amplitude')
        ax.set_yticklabels([])

    plt.tight_layout()
    plt.savefig(f"{name}_physio_resp_plot.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # ------------------ Save to text file ------------------
    physio_data = np.column_stack((time_vector, resp_vector, trigger_vector, pulse_vector))
    #print(os.path.basename(json_fname))
    #print(os.getcwd())
    name = os.path.basename(json_fname).replace('.json', '')
    np.savetxt(f"{name}.physio", physio_data, fmt='%.9f', delimiter='\t')
    print(f"Saved FSL physio file: {name}.physio")
    return time_vector, pulse_vector, trigger_vector, resp_vector


def main():
    parser = get_parser()
    args = parser.parse_args()
    TR = args.TR
    number_of_volumes = args.number_of_volumes
    json_fname = args.json
    resp_fname = args.resp
    pulse_fname = args.pulse

    time_vector, pulse_vector, trigger_vector, resp_vector = create_FSL_physio_text_file_from_Siemens_file(pulse_fname=pulse_fname,
                                                                                                           resp_fname=resp_fname,
                                                                                                           json_fname=json_fname,
                                                                                                           TR=TR, 
                                                                                                           number_of_volumes=number_of_volumes)

if __name__ == '__main__':
    main()