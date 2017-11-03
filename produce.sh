#!/usr/bin/env bash
# use this script to generate noise-mixed data
# the script add_noise.py is used to achieve the noise injection

# define noise type first
noise_prior_white="0,10,0,0"     #define white noise to sample. [S_clean, S_white, S_car, S_cafe]
noise_prior_car="0,0,10,0"       #define car noise to sample. [S_clean, S_white, S_car, S_cafe]
noise_prior_cafe="0,0,0,10"      #define cafe noise to sample. [S_clean, S_white, S_car, S_cafe]
declare -A noise_prior_box=(["white"]=${noise_prior_white} ["car"]=${noise_prior_car} ["cafe"]=${noise_prior_cafe})

seed=32
sigma0=0                         #ensure the SNR is sampled as the value exacted defined by noise_level
verbose=0
noise_level=20
wav_scp="`pwd`/wav_home.scp"
noise_scp="`pwd`/noise_home.scp"

for noise_type in white car cafe; do
  noise_prior="${noise_prior_box["$noise_type"]}"
  output_dir="`pwd`/${noise_type}/${noise_level}"

  echo "producing ${noise_type} data."
  echo "sigma0=${sigma0} noise_level=${noise_level} prior=${noise_prior}"
  mkdir -p $output_dir
  python add_noise.py --seed $seed --sigma0 $sigma0 --noise_level $noise_level   \
	  --verbose $verbose --noise_prior $noise_prior --noise_src $noise_scp  \
	  --wav_src $wav_scp --wav_dir $output_dir || exit
done

echo "All done!"
