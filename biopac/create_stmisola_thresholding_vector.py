#!/usr/bin/env python
# -*- coding: utf-8

# For usage, type: python create_right_left_seg_mask.py -h

# Authors: Kenneth Weber

import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import square


def get_parser():
    parser = argparse.ArgumentParser(
        description="Create Create 1D stimulation vector for BIOPAC stmisola")
    parser.add_argument('-type', default="monophasic", required=False, type=str,
                        help="biphasic or monophasic")
    parser.add_argument('-stim_f', default=100, required=False, type=int,
                        help="Stimulation frequency in Hz")
    parser.add_argument('-stim_pw', default=0.0002, required=False, type=float,
                        help="Stimulation pulse width in seconds")
    parser.add_argument('-stim_duration', default=2, required=False, type=int,
                        help="Duration of stimulation block in seconds.")
    parser.add_argument('-no_stim_duration', default=2, required=False, type=int,
                    help="Duration of no stimulation block in seconds.")
    parser.add_argument('-stim_amps', default='0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.2,2.4,2.6,2.8,3.0,3.2,3.4,3.6,3.8,4.0,4.2,4.4,4.6,4.8,5.0,5.2,5.4,5.6,5.8,6.0,6.2,6.4,6.6,6.8,7.0,7.2,7.4,7.6,7.8,8.0,8.2,8.4,8.6,8.8,9.0,9.2,9.4,9.6,9.8,10.0', required=False, type=str,
                        help="Comma separated amplitudes of BIOPAC stim file in Volts. For example: '0.2,0.4,0.6,0.8,1.0'")
    parser.add_argument('-samp_f', default=5000, required=False, type=int,
                        help="Sampling frequency of stimulation vector in Hz")
    parser.add_argument('-filename', required=False, type=str,
                        help="Filename prefix of outputs")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    try:
       filename
    except:
        filename = args.type + '_f_' + \
            str(args.stim_f) + 'hz_pw_' + \
            str(args.stim_pw) + 's_stim_' + \
            str(args.stim_duration) + 's_no_stim_'+ \
            str(args.no_stim_duration)  + 's_samp_f_' + \
            str(args.samp_f) + 'hz'

    amps=args.stim_amps.split(',')

    n_stim_blocks=len(amps)

    #Create vector of zeros length of stimulation experiment
    stim_vector = np.zeros( ((n_stim_blocks*args.stim_duration) + ((n_stim_blocks+1)*args.no_stim_duration)) *args.samp_f)

    #phase of stimulation wave default is 0
    phase=0

    #create time vector for stim_block
    time=np.arange(0,args.stim_duration, 1/args.samp_f)+phase

    #Raise errors regarding pulse width
    if args.stim_pw/(1/args.stim_f) > 1:
        raise ValueError('Pulse width greater than sampling period. Reduce pulse width for this sampling frequency.')

    if args.stim_pw % (1/args.samp_f) != 0:
        raise ValueError('Pulse width needs to be multiple of sampling period. Adjust pulse width for this sampling frequency.')

    if (args.type.lower() == 'biphasic') & ((args.stim_pw * args.samp_f) % 2 != 0):
        raise ValueError('Duration of pulse width not possible with biphasic and current sampling frequency. Adjust pulse width or sampling frequency.')

    stim_vector_key=np.empty([n_stim_blocks,3])

    for block in np.arange(1, (n_stim_blocks)+1):
        #pw/1/sampling_f = duty cycle
        if args.type.lower() == 'biphasic':
            #Noticed some interpolation erros with using square function, so rewrote not using square function
            #stim_block=float(amps[block-1])*(square((2 * np.pi * args.stim_f * time), args.stim_pw/(1/args.stim_f))) 
            single_stim_block = np.zeros(int((1/args.stim_f)*args.samp_f))
            single_stim_block[:int(args.stim_pw/2*args.samp_f)] = 1
            single_stim_block[int(args.stim_pw/2*args.samp_f):int(args.stim_pw/2*args.samp_f)+int(args.stim_pw/2*args.samp_f)] = -1
            stim_block = float(amps[block-1])*np.tile(single_stim_block, args.stim_duration*args.stim_f)

        elif args.type.lower() == 'monophasic':
            #Noticed some interpolation erros with using square function, so rewrote not using square function
            #stim_block=float(amps[block-1])*((square((2 * np.pi * args.stim_f * time), args.stim_pw/(1/args.stim_f)) + 1)/2)
            single_stim_block = np.zeros(int((1/args.stim_f)*args.samp_f))
            single_stim_block[:int(args.stim_pw*args.samp_f)] = 1
            stim_block = float(amps[block-1])*np.tile(single_stim_block, args.stim_duration*args.stim_f)

        else:
            raise ValueError('Biphasic or monophasic not specified correctly.')

        block_start=(block*args.samp_f*args.no_stim_duration) + ((block-1)*args.samp_f*args.stim_duration)
        stim_vector[block_start:block_start+(args.stim_duration*args.samp_f)]=stim_block

        #Create key for knowing stimulation amplitude of each block based on time
        stim_vector_key[block-1,0] = amps[block-1] #amp
        stim_vector_key[block-1,1] = block_start/args.samp_f #block start in seconds
        stim_vector_key[block-1,2] = (block_start+(args.stim_duration*args.samp_f))/args.samp_f  #block end in seconds
   
    plt.plot(np.arange(0,len(stim_vector)/args.samp_f, 1/args.samp_f), stim_vector, linewidth=0.001)
    plt.xlabel("Seconds")
    plt.ylabel("mA")
    plt.savefig('thresholding_vector_' + filename + '.pdf', dpi=1000)
    plt.close()

    np.savetxt('thresholding_vector_' + filename + '.txt', stim_vector, fmt='%.1f\n', newline='')

    np.savetxt('thresholding_vector_' + filename + '.key', stim_vector_key, fmt='%.1f\t%.0f\t%.0f\n', newline='', header='amp\tstart\tend\n')

if __name__ == '__main__':
    main()
    