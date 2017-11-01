'''
    This model mix given noise wav and original wav file.
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
    for i in xrange(len(mat)):
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
    for x in xrange(1, len(samples)):
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

def wave_mat(fname):
    with wave.open(fname, 'r') as wav:
        num = wav.getnframes()
        data = wav.readframes(num)
        return list(struct.unpack('{}h'.format(num), data))

def wave_header(sample_array, sample_rate):
    byte_count = (len(sample_array)) * 2                            # short
    header = struct.pack('<ccccIccccccccIHHIIHH',
                      'R', 'I', 'F', 'F',
                      byte_count + 0x2c - 8,                        # header size
                      'W', 'A', 'V', 'E', 'f', 'm', 't', ' ',
                      0x10,                                         # size of 'fmt ' header
                      1,                                            # format 1
                      1,                                            # channels
                      sample_rate,                                  # samples / second
                      sample_rate * 2,                              # bytes / second
                      2,                                            # block alignment
                      16)                                           # bits / sample
    header += struct.pack('<ccccI',
                       'd', 'a', 't', 'a', byte_count)
    return header

def output(tag, mat):
    sys.stdout.write(tag + ' ')
    sys.stdout.write(wave_header(mat, 16000))
    sys.stdout.write(struct.pack('{}h'.format(len(mat)), *mat))

def output_wave_file(dir, tag, mat):
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open('{}/{}'.format(dir, tag), 'w') as file:
        file.write(wave_header(mat, 16000))
        file.write(struct.pack('{}h'.format(len(mat)), *mat))

def main():
    parser = optparse.OptionParser()
    parser.add_option('--noise_level', type=float, help='')
    parser.add_option('--noise_src', type=str, help='')
    parser.add_option('--noise_prior', type=str, help='')
    parser.add_option('--seed', type=int, help='')
    parser.add_option('--sigma0', type=float, help='')
    parser.add_option('--verbose', type=int, help='')
    parser.add_option('--wav_src', type=str, help='')
    parser.add_option('--wav_dir', type=str, help='')
    (args, dummy) = parser.parse_args()
    random.seed(args.seed)
    params = [float(x) for x in args.noise_prior.split(',')]

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    global noises
    noise_energies = [0.]
    noises = [(0, [])]
    for tag, wav in scp(args.noise_src):
        # logging.debug('noise wav: %s', wav)
        mat = wave_mat(wav)
        eng = energy(mat)
        # logging.debug('noise energy: %f', e)
        noise_energies.append(eng)
        noises.append((0, mat))

    for tag, wav in scp(args.wav_src):
        # logging.debug('wav: %s', wav)
        noise_level = random.gauss(args.noise_level, args.sigma0)
        # logging.debug('noise level: %f', noise_level)
        mat = wave_mat(wav)
        signal = energy(mat)
        # logging.debug('signal energy: %f', signal)
        noise = signal / (10 ** (noise_level / 10.))
        # logging.debug('noise energy: %f', noise)
        type = dirichlet(params)
        # logging.debug('selected type: %d', type)
        fname = os.path.basename(wav)
        if type == 0:
            if args.wavdir != 'NULL':
                output_wave_file(args.wavdir, fname, mat)
            else:
                output(tag, mat)
        else:
            p, n = noises[type]
            #print("p: {}".format(p))
            if p + len(mat) > len(n):
                noise_energies[type] = energy(n[p::] + n[0:len(n) - p:])
            else:
                noise_energies[type] = energy(n[p:p + len(mat):])
            #print("noise: {}  noise_energy: {}  type: {}".format(noise, noise_energies[type], type))
            scale = math.sqrt(noise / noise_energies[type])
            #print("scale: {}".format(scale))
            #logging.debug('noise scale: %f', scale)
            pos, result = mix(mat, n, p, scale)
            noises[type] = (pos, n)
            if args.wavdir != 'NULL':
                output_wave_file(args.wavdir, fname, result)
            else:
                output(tag, result)

if __name__ == '__main__':
    main()
