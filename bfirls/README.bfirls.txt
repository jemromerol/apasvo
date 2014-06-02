This directory contains estimations of the noise power spectral density of sets of natural earthquakes.
You can use them to generate synthetic earthquakes contaminated with realistic-like seismic noise.

E.g. Given two seismic signals, 'meq.bin' and 'meq2.txt', sample rate 50 Hz, adds
background noise of 2.0 dB. Noise is modeled by a FIR filter whose
coefficients are stored in the file 'IAGPDS-bfirls.txt'.
Results will be saved to 'eq00.out' and 'eq01.out'.

    python apasvo-generator.py meq.bin meq2.txt -f 50 -np 2 -fir IAGPDS-bfirls.txt

For the estimation method of the background seismic noise see:

> Peterson, J. (1993). Observations and modeling of seismic background noise.
