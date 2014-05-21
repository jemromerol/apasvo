# encoding: utf-8
'''
@author:     Jose Emilio Romero Lopez

@copyright:  Copyright 2013-2014, Jose Emilio Romero Lopez.

@license:    GPL

@contact:    jemromerol@gmail.com

  This file is part of APASVO.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import numpy as np
from scipy import signal

from apasvo.utils.formats import rawfile


def gutenberg_richter(b=1.0, size=1, m_min=2.0, m_max=None):
    """Generates a random sequence of earthquake magnitudes
    according to Gutenberg-Richter law.

    See:
    BAKER, Jack W. An introduction to probabilistic seismic hazard analysis (PSHA).
    White paper, version, 2008, vol. 1.

    Args:
        b: A parameter that measures the relative ratio between small and large
            magnitudes in a region. Default value is 1.0.
        size: Size of the generated sequence. Default value is 1.
        m_min: Minimum magnitude considered. Default: 2.0.
        m_max: Upper bound of earthquake magnitudes.
            Default value is None, which means no upper limit is considered.

    Returns:
        out: A list of random earthquake magnitudes.
    """
    if m_max:
        bound_term = 1.0 - 10 ** (-b * (m_max - m_min))
    else:
        bound_term = 1.0
    return m_min - np.log10(-np.random.rand(size) * bound_term + 1.0) / b


def generate_artificial_earthquake(tmax, t0, fs, P_signal_db, P_noise_db,
                                   bfirls=None, low_period=50., high_period=10.,
                                   bandwidth=4., overlap=1., f_low=2.,
                                   f_high=18., low_amp=.2, high_amp=.1):
    """Generates a synthetic earthquake signal with background noise.

    An artificial earthquake is generated at the desired start point from
    white noise band-filtered and modulated by using different envelope
    functions for each band.
    Similarly, background noise is modeled from white noise and finally
    added to the previously generated sequence that contains the synthetic
    earthquake.

    Args:
        tmax: Length of the generated signal in seconds.
        t0: Start time of the earthquake in seconds from the beginning
            of the signal.
        fs: Sample rate in Hz.
        P_signal_db: Earthquake power in dB.
        P_noise_db: Background noise power in dB.
        bfirls: A list of coefficients of a FIR filter that models the
            background noise. See:

            Peterson, J. (1993). Observations and modeling of seismic
            background noise.

            Default value is None, which means unfiltered white noise is used
                to model the background noise.
        low_period: Start value of the range of noise envelope lengths
            for the different bands at the multi-band synthesis.
            Default: 50 seconds.
        high_period: End value of the range of noise envelope lengths
            for the different bands at the multi-band synthesis.
            Default: 10 seconds.
        bandwidth: Bandwidth of each band at the multi-band synthesis.
            Default: 4 Hz.
        overlap: Overlap between bands at the multi-band synthesis.
            Default: 1 Hz.
        f_low: Start frequency at the multi-band synthesis.
            Default: 2 Hz.
        f_high: End frequency at the multi-band synthesis.
            Default: 18 Hz.
        low_amp: Start value of the range of noise envelope amplitudes
            for the different bands at the multi-band synthesis.
            Default: 0.2.
        high_amp: End value of the range of noise envelope amplitudes
            for the different bands at the multi-band synthesis.
            Default: 0.1.

    Returns:
        out: A numpy array containing the generated signal.
    """
    # Earthquake generation
    artificial_earthquake = generate_seismic_earthquake(tmax, t0, fs,
                                                        P_signal_db,
                                                        low_period,
                                                        high_period,
                                                        bandwidth,
                                                        overlap,
                                                        f_low, f_high,
                                                        low_amp, high_amp)
    # Noise generation
    background_noise = generate_seismic_noise(tmax, fs, P_noise_db, bfirls)
    return artificial_earthquake + background_noise


def generate_seismic_earthquake(tmax, t0, fs, P_signal_db, low_period,
                                   high_period, bandwidth, overlap,
                                   f_low, f_high, low_amp, high_amp):
    """Generates a synthetic earthquake signal.

    An artificial earthquake is generated at the desired start point from
    white noise band-filtered and modulated by using different envelope
    functions for each band.

    Args:
        tmax: Length of the generated signal in seconds.
        t0: Start time of the earthquake in seconds from the beginning
            of the signal.
        fs: Sample rate in Hz.
        P_signal_db: Earthquake power in dB.
        low_period: Start value of the range of noise envelope lengths
            for the different bands at the multi-band synthesis.
        high_period: End value of the range of noise envelope lengths
            for the different bands at the multi-band synthesis.
        bandwidth: Bandwidth of each band at the multi-band synthesis.
        overlap: Overlap between bands at the multi-band synthesis.
        f_low: Start frequency at the multi-band synthesis.
        f_high: End frequency at the multi-band synthesis.
        low_amp: Start value of the range of noise envelope amplitudes
            for the different bands at the multi-band synthesis.
        high_amp: End value of the range of noise envelope amplitudes
            for the different bands at the multi-band synthesis.

    Returns:
        out: A numpy array containing the generated signal.
    """
    if fs <= 0:
        raise ValueError("fs must be a positive value")
    # Signal length in the range 0:1/fs:tmax
    L = int(tmax * fs) + 1
    # First earthquake sample
    n0 = int(t0 * fs)
    if n0 >= L:
        raise ValueError("Generated earthquake must start before the end of the signal.")
    # Value from which the exponential function truncates its fall
    betta = high_amp / 100.

    # We generate the artificial earthquake from white noise band-filtered
    # and modulated by using different envelope functions
    w_noise = np.random.randn(L)
    f_filt_low = np.arange(f_low, f_high - bandwidth, bandwidth - overlap)
    f_filt_high = f_filt_low + bandwidth
    N_filt = len(f_filt_low)  # N. of applied filters
    # Matrix where each column has a band noise
    noise_band = np.zeros((N_filt, L))
    for i in xrange(N_filt):
        b, a = signal.butter(2,
                             [f_filt_low[i] / (fs / 2.),
                              f_filt_high[i] / (fs / 2.)], btype='bandpass')
        noise_band[i, :] = signal.lfilter(b, a, w_noise)
    # Length of noise envelope for the different bands
    filt_len = np.linspace(low_period, high_period, N_filt)
    n1 = np.round(n0 + filt_len * fs)
    # Amplitude of noise envelope for the different bands
    filt_amp = np.linspace(low_amp, high_amp, N_filt)
    # By using amplitude and length of the noise envelopes we can obtain
    # the alpha decay constant
    # The exponential form is A0*exp(-alpha(n-n0)). In n=n0 its value is A0
    # If we want
    alpha = -np.log(betta / filt_amp) / (n1 - n0)
    # Generate the signal envelope
    noise_env = np.zeros((N_filt, L))
    for i in xrange(N_filt):
        end = np.minimum(L, n1[i])
        noise_env[i, n0:end] = (filt_amp[i] *
                                  np.exp(-alpha[i] *
                                         (np.arange(n0, end) - n0)))
    # We multiply the envelope for each noise band
    noise_band_envelope = noise_band * noise_env
    artificial_earthquake = np.sum(noise_band_envelope, 0)
    eq_pw_db = 10 * np.log10(np.var(artificial_earthquake[n0:n0 + 5 * fs]))
    # We want the earthquake has a power in dB given by P_signal_db
    gamma_signal = 10 ** ((P_signal_db - eq_pw_db) / 20)
    artificial_earthquake = gamma_signal * artificial_earthquake
    return artificial_earthquake


def generate_seismic_noise(tmax, fs, P_noise_db, bfirls=None):
    """Generates a seismic background noise signal.

    Args:
        tmax: Length of the generated signal in seconds.
        fs: Sample rate in Hz.
        P_noise_db: Background noise power in dB.
        bfirls: A list of coefficients of a FIR filter that models the
            background noise. See:

            Peterson, J. (1993). Observations and modeling of seismic
            background noise.

            Default value is None, which means unfiltered white noise is used
                to model the background noise.

    Returns:
        out: A numpy array containing the generated signal.
    """
    if fs <= 0:
        raise ValueError("fs must be a positive value")
    if bfirls is None:
        bfirls = np.array([1])
    # Signal length in the range 0:1/fs:tmax
    L = int(tmax * fs) + 1
    # White noise generation for polluting the earthquake
    # We add noise according to Peterson's Model
    x = np.random.randn(L)
    background_noise = signal.lfilter(bfirls, 1, x)
    # We want the white noise has a power in dB given by P_noise_db
    bg_noise_pow_db = 10 * np.log10(np.var(background_noise))
    gamma_noise = 10 ** ((P_noise_db - bg_noise_pow_db) / 20)
    background_noise = gamma_noise * background_noise
    return background_noise


class EarthquakeGenerator(object):
    """A class that generates synthetic earthquake signals.

    Attributes:
        bfirls: A list of coefficients of a FIR filter that models the
            background noise. See:

            Peterson, J. (1993). Observations and modeling of seismic
            background noise.

            Default value is None, which means unfiltered white noise is used
                to model the background noise.
        fs: Sample rate in Hz.
        P_noise_db: Background noise power in dB.
        low_period: Start value of the range of noise envelope lengths
            for the different bands at the multi-band synthesis.
            Default: 50 seconds.
        high_period: End value of the range of noise envelope lengths
            for the different bands at the multi-band synthesis.
            Default: 10 seconds.
        bandwidth: Bandwidth of each band at the multi-band synthesis.
            Default: 4 Hz.
        overlap: Overlap between bands at the multi-band synthesis.
            Default: 1 Hz.
        f_low: Start frequency at the multi-band synthesis.
            Default: 2 Hz.
        f_high: End frequency at the multi-band synthesis.
            Default: 18 Hz.
        low_amp: Start value of the range of noise envelope amplitudes
            for the different bands at the multi-band synthesis.
            Default: 0.2.
        high_amp: End value of the range of noise envelope amplitudes
            for the different bands at the multi-band synthesis.
            Default: 0.1.
    """

    def __init__(self, bfirls=None, fs=50.0, P_noise_db=0.0,
                 low_period=50.0, high_period=10.0, bandwidth=4.0,
                 overlap=1.0, f_low=2.0, f_high=18.0,
                 low_amp=0.2, high_amp=0.1, **kwargs):
        super(EarthquakeGenerator, self).__init__()
        self.bfirls = bfirls
        self.fs = fs
        self.P_noise_db = P_noise_db
        self.low_period = low_period
        self.high_period = high_period
        self.bandwidth = bandwidth
        self.overlap = overlap
        self.f_low = f_low
        self.f_high = f_high
        self.low_amp = low_amp
        self.high_amp = high_amp

    def load_noise_coefficients(self, fileobj, dtype='float64',
                                byteorder='native'):
        """Loads 'bfirls' attribute from a given file.

        File must be on binary or plain text format.

        Args:
            fileobj: A binary or text file object containing a list of numeric
                coefficients.
            dtype: Data-type of the numeric data stored into the file.
            byteorder: Byte-order of the numeric data stored into the file.
        """
        fhandler = rawfile.get_file_handler(fileobj, dtype=dtype,
                                            byteorder=byteorder)
        self.bfirls = fhandler.read()

    def generate_events(self, t_average, t_max, b=1.0,
                               m_min=2.0, m_max=7.0):
        """Generates a random sequence of seismic events from initial
        time zero to a given maximum time.

        Events are described by their time of occurrence and magnitude.

        The time interval between events is generated by using a Poisson
        distribution, while their magnitudes are generated according to
        Gutenberg-Richter's law. The number of generated events may vary
        between function calls even if the same parameters are used.

        Args:
            t_average: Average time between two consecutive events.
            t_max: Maximum time.
            b: A parameter that measures the relative ratio between small and
                large magnitudes in a region. Default value is 1.0.
            m_min: Minimum magnitude considered. Default: 2.0.
            m_max: Upper bound of earthquake magnitudes.
                If value is None then no upper limit is considered.
                Default: 7.0.

        Returns:
            event_t: Times list of the generated events.
            event_m: Magnitudes list of the generated events.
        """
        event_t = []
        t = np.random.poisson(t_average)
        while t < t_max:
            event_t.append(t)
            t += np.random.poisson(t_average)
        event_m = gutenberg_richter(b, len(event_t), m_min, m_max)
        return np.array(event_t), event_m

    def generate_nevents(self, t_average, event_n, b=1.0,
                               m_min=2.0, m_max=7.0):
        """Generates a random list of seismic events of a given size.

        Events are described by their time of occurrence and magnitude.

        The time interval between events is generated by using a Poisson
        distribution, while their magnitudes are generated according to
        Gutenberg-Richter's law.

        Args:
            t_average: Average time between two consecutive events.
            event_n: Number of events generated.
            b: A parameter that measures the relative ratio between small and
                large magnitudes in a region. Default value is 1.0.
            m_min: Minimum magnitude considered. Default: 2.0.
            m_max: Upper bound of earthquake magnitudes.
                If value is None then no upper limit is considered.
                Default: 7.0.

        Returns:
            event_t: Times list of the generated events.
            event_m: Magnitudes list of the generated events.
        """
        event_t = np.cumsum(np.random.poisson(t_average, event_n))
        event_m = gutenberg_richter(b, event_n, m_min, m_max)
        return event_t, event_m

    def generate_earthquake(self, t_max, t0, p_eq):
        """Generates a synthetic earthquake with background noise.

        Args:
            t_max: Length of the generated signal in seconds.
            t0: Start time of the earthquake in seconds from the beginning
                of the signal in seconds.
            p_eq: Earthquake power in dB.

        Returns:
            out: A numpy array containing the generated signal.
        """
        return generate_artificial_earthquake(t_max, t0, self.fs, p_eq,
                                              self.P_noise_db, self.bfirls,
                                              self.low_period,
                                              self.high_period,
                                              self.bandwidth, self.overlap,
                                              self.f_low, self.f_high,
                                              self.low_amp, self.high_amp)

    def generate_noise(self, eq):
        """Adds background noise to a given seismic signal.

        Args:
            eq: A seismic signal, numpy array type.

        Returns:
            out: Generated signal, numpy array type.
        """
        noise = generate_seismic_noise(len(eq) / self.fs, self.fs, self.P_noise_db,
                                       self.bfirls)
        return noise + eq
