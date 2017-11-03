# noise-mixer

Noise-mixer is an useful data generate tool writen by Python 2.7, which can mix noise wav to your origin clear wav file. 

By generating noisy audio file, Noise-mixer can help you get more training data when train an **ASR**(automatic speech recognition) system. 

## How to use it

It's easy to generate audio file(wav file) by noise-mixer, what you need to do is:

1. Prepare noise wav list, which including all noise wav in this format: 

> name path

sample like:

![noise_scp](/img/noise.jpg)

2. Perpare origin clear wav list in this format:

> name path

sample like:

![wav_scp](/img/wav.jpg)

3. Edit `produce.sh` to change your output directory, noise_home, wav_home and noise level and so on. 
4. Then run `produce.sh`, wait a moment for the output.
5. Done !

## Note

This tool is developed by Python 2.7, it doesn't work for Python 3.*

