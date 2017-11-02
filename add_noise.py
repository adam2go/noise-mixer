#!/usr/bin/env python
'''
    This module mix given noise wav and original wav file.
'''

from __future__ import print_function
import optparse
import random
import bisect
import logging
import wave
import math
import struct
import sys
import os

'''
    Description: Calculate wave file energy
    Inputs:
        mat: wav data matrix
    Outputs:
        wav file energy
'''
def energy(mat):
    return float(sum([x * x for x in mat])) / len(mat)

'''
    Description: Mix origin clear wav and noise wav
    Inputs:
        mat: clear wav data matrix
        noise: noise wav data matrix
        pos: noise wav frame's position
        scale: scale of clear and noise wav energy
    Outputs:
        pos: current noise matrix index
        ret: mixed wav matrix
'''
def mix(mat, noise, pos, scale):
    ret = []
    l = len(noise)
    for i in range(len(mat)):
        frm = mat[i]
        tmp = int(frm + scale * noise[pos])
        tmp = max(min(tmp, 32767), -32768)
        ret.append(tmp)
        pos += l
        if pos == l:
            pos =0
    return (pos, ret)

'''
    Description: Calculate noise type with given parameters
    Inputs:
        params: noise prior parameters
    Outputs:
        noise type
'''
def dirichlet(params):
    samples = [random.gammavariate(x, 1) if x > 0 else 0. for x in params]
    samples = [x / sum(samples) for x in samples]
    for x in range(1, len(samples)):
        samples[x] += samples[x - 1]
    return bisect.bisect_left(samples, random.random())

'''
    Description: yield wav tag and wav path from scp file
    Inputs:
        fname: scp file's name, scp file should like this:
            ...
            SPK0001_1 /data2/SPK_0001/SPK0001_1.wav
            SPK0001_2 /data2/SPK_0001/SPK0001_2.wav
            SPK0001_3 /data2/SPK_0001/SPK0001_3.wav
            ...
    Outputs:
        tuple of wav tag and wav path
'''
def scp(fname):
    with open(fname, 'r') as file:
        for line in file:
            yield tuple(line.strip().split())

'''
    Description: generate int type matrix for given wav file
    Inputs:
        fname: wav file name
    Outputs:
        matrix of the wav file
'''
def wave_mat(fname):
    with wave.open(fname, 'r') as wav:
        num = wav.getnframes()
        data = wav.readframes(num)
        return list(struct.unpack('{}h'.format(num), data))

'''
    Description: generate wav header
    Inputs:
        mat: wav matrix
        rate: wav frame rate
    Outputs:
        packed wav header
'''
def wave_header(mat, rate):
    byte_count = (len(mat)) * 2                                     # short type
    header = struct.pack('<ccccIccccccccIHHIIHH',
                      'R', 'I', 'F', 'F',
                      byte_count + 0x2c - 8,                        # header size
                      'W', 'A', 'V', 'E', 'f', 'm', 't', ' ',
                      0x10,                                         # size of 'fmt ' header
                      1,                                            # format 1
                      1,                                            # channels
                      rate,                                         # samples / second
                      rate * 2,                                     # bytes / second
                      2,                                            # block alignment
                      16)                                           # bits / sample
    header += struct.pack('<ccccI',
                       'd', 'a', 't', 'a', byte_count)
    return header

'''
    Description: output wav file (string type) if file directory didn't given
    Inputs:
        tag: wav file name/tag
        mat: wav matrix
    Outputs:
        string type wav file
'''
def output(tag, mat):
    sys.stdout.write(tag + ' ')
    sys.stdout.write(wave_header(mat, 16000))
    sys.stdout.write(struct.pack('{}h'.format(len(mat)), *mat))

'''
    Description: output wav file (wav type) to given directory
    Inputs:
        dir: output directory
        tag: wav file name/tage
        mat: wav matrix
    Outputs:
        wav type file
'''
def output_wave_file(dir, tag, mat):
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open('{}/{}'.format(dir, tag), 'w') as file:
        file.write(wave_header(mat, 16000))
        file.write(struct.pack('{}h'.format(len(mat)), *mat))


def main():
    parser = optparse.OptionParser()
    parser.add_option('--seed', type=int, default=64)
    parser.add_option('--sigma0', type=float, default=0)
    parser.add_option('--verbose', type=int, default=0)
    parser.add_option('--wav_src', type=str)
    parser.add_option('--wav_dir', type=str)
    parser.add_option('--noise_src', type=str)
    parser.add_option('--noise_prior', type=str)
    parser.add_option('--noise_level', type=float)
    (args, dummy) = parser.parse_args()
    random.seed(args.seed)
    logging.debug('{}'.format(args.noise_prior))
    params = [float(x) for x in args.noise_prior.split(',')]

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    global noises
    noise_energies = [0.]
    noises = [(0, [])]
    for tag, wav in scp(args.noise_src):
        mat = wave_mat(wav)
        eng = energy(mat)
        noise_energies.append(eng)
        noises.append((0, mat))

    for tag, wav in scp(args.wav_src):
        noise_level = random.gauss(args.noise_level, args.sigma0)
        mat = wave_mat(wav)
        signal = energy(mat)
        noise = signal / (10 ** (noise_level / 10.))
        type = dirichlet(params)
        fname = os.path.basename(wav)
        if type == 0:
            if args.wav_dir != 'NULL':
                output_wave_file(args.wav_dir, fname, mat)
            else:
                output(tag, mat)
        else:
            p, n = noises[type]
            if p + len(mat) > len(n):
                noise_energies[type] = energy(n[p::] + n[0:len(n) - p:])
            else:
                noise_energies[type] = energy(n[p:p + len(mat):])
            scale = math.sqrt(noise / noise_energies[type])
            pos, result = mix(mat, n, p, scale)
            noises[type] = (pos, n)
            if args.wav_dir != 'NULL':
                output_wave_file(args.wav_dir, fname, result)
            else:
                output(tag, result)

if __name__ == '__main__':
    main()
