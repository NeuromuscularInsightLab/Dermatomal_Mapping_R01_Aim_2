#!/usr/bin/env python
# -*- coding: utf-8

# For usage, type: python create_right_left_seg_mask.py -h

# Authors: Kenneth Weber

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import square
import tkinter as tk
from tkinter import simpledialog
from tkinter import filedialog
import time

def get_parser():
    parser = argparse.ArgumentParser(
        description="Create Create 1D stimulation vector for BIOPAC stmisola. To run type: create_aim_1_stmisola_stimulation_vector.py -stim_amp_low #.# -stim_amp_high #.# -subject_id sub-DMAim1HC###")
    parser.add_argument('-type', default='monophasic', required=False, type=str,
                        help="biphasic or monophasic")
    parser.add_argument('-stim_f', default=100, required=False, type=int,
                        help="Stimulation frequency in Hz")
    parser.add_argument('-stim_pw', default=0.0002, required=False, type=float,
                        help="Stimulation pulse width in seconds")
    parser.add_argument('-stim_duration', default=5, required=False, type=int,
                        help="Duration of stimulation block in seconds.")
    parser.add_argument('-no_stim_durations', default='2,2,2,2,2,2,4,4,4,4,4,4,6,6,6,6,6,6,8,8,8,8,8,8,10,10,10,10,10,10', required=False, type=str,
                    help="Duration of no stimulation blocks in seconds.")
    parser.add_argument('-stim_amps', default='0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.2,2.4,2.6,2.8,3.0,3.2,3.4,3.6,3.8,4.0,4.2,4.4,4.6,4.8,5.0,5.2,5.4,5.6,5.8,6.0,6.2,6.4,6.6,6.8,7.0,7.2,7.4,7.6,7.8,8.0,8.2,8.4,8.6,8.8,9.0,9.2,9.4,9.6,9.8,10.0', required=False, type=str,
                        help="Stimulation amplitude")
    parser.add_argument('-n_stim_blocks', default=30, required=False, type=int,
                        help="Number of stimulation blocks per stimulation amplitude")
    parser.add_argument('-samp_f', default=5000, required=False, type=int,
                        help="Sampling frequency of stimulation vector in Hz")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    save_directory = os.getcwd()
    
    os.makedirs(os.path.join(save_directory, 'biopac_stim_vectors'), exist_ok=True)
    os.makedirs(os.path.join(save_directory, 'fsl_stim_vectors'), exist_ok=True)
    
    #Create stim_amps list
    stim_amps=args.stim_amps.split(',')

    #Convert to float
    stim_amps = [float(stim_amp) for stim_amp in stim_amps]

    #Create no_stim_duration list and then shuffle
    no_stim_durations=args.no_stim_durations.split(',')
    
    #Convert to integer
    no_stim_durations = [int(duration) for duration in no_stim_durations]

    #Get total no stim duration
    no_stim_duration=0
    for duration in no_stim_durations:
        no_stim_duration = no_stim_duration + duration

    #Raise error if n_stim_blocks > than no_stim_durations
    if args.n_stim_blocks > len(no_stim_durations):
        raise ValueError('Error number of stimulation blocks is greater than number of no_stim_durations.')

    for stim_amp in stim_amps:

        #Raise error if stim_amp_high > 10.0
        if stim_amp > 10.0 or stim_amp <= 0:
            raise ValueError('Error with stim amp.')


        filename = args.type + '_f_' + \
            str(args.stim_f) + 'hz_pw_' + \
            str(args.stim_pw) + 's_stim_' + \
            str(args.stim_duration) + 's_'+ \
            str(args.n_stim_blocks)  + '_stim_blocks_' + \
            str(stim_amp)  + 'ma_samp_f_' + \
            str(args.samp_f)  + 'hz'
        print(filename)

        #Create random generator setting seed equal to amplitude*100 and then shuffle no_stim_durations
        rng = np.random.default_rng(seed=int(stim_amp*100))
        rng.shuffle(no_stim_durations)

        #Create vector of zeros length of stimulation experiment
        stim_vector = np.zeros(((args.n_stim_blocks*args.stim_duration)+no_stim_duration)*args.samp_f)
        fsl_stim_vector = np.zeros(((args.n_stim_blocks*args.stim_duration)+no_stim_duration)*100) #Using 100 Hz sampling frequency for fsl vector
        
        #Phase of stimulation wave default is 0
        phase=0

        #create time vector for stim_block
        #time=np.arange(0,args.stim_duration, 1/args.samp_f)+phase
        fsl_time=np.arange(0,args.stim_duration, 1/100)+phase #Using 100 Hz sampling frequency for fsl vector

        #Raise errors regarding pulse width
        if args.stim_pw/(1/args.stim_f) > 1:
            raise ValueError('Pulse width greater than sampling period. Reduce pulse width for this sampling frequency.')
        
        if args.stim_pw % (1/args.samp_f) != 0:
            raise ValueError('Pulse width needs to be multiple of sampling period. Adjust pulse width for this sampling frequency.')

        if (args.type.lower() == 'biphasic') & ((args.stim_pw * args.samp_f) % 2 != 0):
            raise ValueError('Duration of pulse width not possible with biphasic and current sampling frequency. Adjust pulse width or sampling frequency.')

        for block in np.arange(0, args.n_stim_blocks):
            #pw/1/sampling_f = duty cycle
            if args.type.lower() == 'biphasic':
                #Noticed some interpolation erros with using square function, so rewrote not using square function
                #stim_block=float(amps[block])*(square((2 * np.pi * args.stim_f * time), args.stim_pw/(1/args.stim_f))) 
                single_stim_block = np.zeros(int((1/args.stim_f)*args.samp_f))
                single_stim_block[:int(args.stim_pw/2*args.samp_f)] = 1
                single_stim_block[int(args.stim_pw/2*args.samp_f):int(args.stim_pw/2*args.samp_f)+int(args.stim_pw/2*args.samp_f)] = -1
                stim_block = stim_amp*np.tile(single_stim_block, args.stim_duration*args.stim_f)

            elif args.type.lower() == 'monophasic':
                #Noticed some interpolation erros with using square function, so rewrote not using square function
                #stim_block=float(amps[block])*((square((2 * np.pi * args.stim_f * time), args.stim_pw/(1/args.stim_f)) + 1)/2)
                single_stim_block = np.zeros(int((1/args.stim_f)*args.samp_f))
                single_stim_block[:int(args.stim_pw*args.samp_f)] = 1
                stim_block = stim_amp*np.tile(single_stim_block, args.stim_duration*args.stim_f)

            else:
                raise ValueError('Biphasic or monophasic not specified correctly.')
            
            #Start with no stimulation before first no stimulation block (block == 0)
            if block == 0:
                block_start= no_stim_durations[block]*args.samp_f
                fsl_block_start= no_stim_durations[block]*100 #Using 100 Hz sampling frequency for fsl vector

            else:
                block_start = block_start + ((no_stim_durations[block] + args.stim_duration) *args.samp_f)
                fsl_block_start = fsl_block_start + ((no_stim_durations[block] + args.stim_duration) * 100) #Using 100 Hz sampling frequency for fsl vector

            stim_vector[block_start:block_start+(args.stim_duration*args.samp_f)]=stim_block

            fsl_stim_block=np.ones(len(fsl_time))

            fsl_stim_vector[fsl_block_start:fsl_block_start+(args.stim_duration*100)]=fsl_stim_block #Using 100 Hz sampling frequency for fsl vector

        #Patch because getting high amlitude values    
        stim_vector[stim_vector > stim_amp] = 0

        plt.plot(np.arange(0,len(stim_vector)/args.samp_f, 1/args.samp_f), stim_vector, linewidth=0.001)
        plt.xlabel("Seconds")
        plt.ylabel("mA")
        plt.savefig(os.path.join(save_directory, 'biopac_stim_vectors', 'biopac_stim_vector_' + filename + '.pdf'))
        plt.close()
        np.savetxt(os.path.join(save_directory, 'biopac_stim_vectors', 'biopac_stim_vector_' + filename + '.txt'), stim_vector, fmt='%.1f\n', newline='')

        fsl_vector = np.concatenate([np.arange(0,len(fsl_stim_vector)/100, 1/100).reshape((-1, 1)), (np.ones(len(fsl_stim_vector))/100).reshape(-1, 1), (fsl_stim_vector).reshape(-1, 1)], axis=1)

        plt.plot(np.arange(0,len(fsl_stim_vector)/100, 1/100), fsl_stim_vector, linewidth=0.001)  #Using 100 Hz sampling frequency for fsl vector
        plt.xlabel("Seconds")
        plt.ylabel("AU")
        plt.savefig(os.path.join(save_directory, 'fsl_stim_vectors', 'fsl_stim_vector_' + filename + '.pdf'))
        plt.close()
        np.savetxt(os.path.join(save_directory, 'fsl_stim_vectors', 'fsl_stim_vector_' + filename + '.txt'), fsl_vector, fmt='%.2f\t%.2f\t%d\n', newline='')
        
        stim_starts = np.where((fsl_vector[:,2][:-1]==0) & (fsl_vector[:,2][1:]==1))[0] + 1

        for stim_index in np.arange(0,len(stim_starts)):
            
            fsl_single_stim_vector = fsl_vector[:,2]*0
            fsl_single_stim_vector[stim_starts[stim_index]:stim_starts[stim_index]+(args.stim_duration*100)]=1

            fsl_single_stim_vector = np.concatenate([np.arange(0,len(fsl_stim_vector)/100, 1/100).reshape((-1, 1)), (np.ones(len(fsl_stim_vector))/100).reshape(-1, 1), fsl_single_stim_vector.reshape(-1, 1)], axis=1)

            plt.plot(np.arange(0,len(fsl_stim_vector)/100, 1/100), fsl_single_stim_vector[:,2], linewidth=0.001)  #Using 100 Hz sampling frequency for fsl vector
            plt.xlabel("Seconds")
            plt.ylabel("AU")
            plt.savefig(os.path.join(save_directory, 'fsl_stim_vectors', 'fsl_stim_vector_' + filename + '_stim_' + str(stim_index+1) + '.pdf'))
            plt.close()
            np.savetxt(os.path.join(save_directory, 'fsl_stim_vectors', 'fsl_stim_vector_' + filename + '_stim_' + str(stim_index+1) + '.txt'), fsl_single_stim_vector, fmt='%.2f\t%.2f\t%d\n', newline='')

if __name__ == '__main__':
    main()
    
