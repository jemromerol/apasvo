# encoding: utf-8
'''
@author:     Jose Emilio Romero Lopez

@copyright:  2013 organization_name. All rights reserved.

@license:    LGPL

@contact:    jemromerol@gmail.com

  This file is part of AMPAPicker.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Lesser General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import numpy as np
from scipy import signal

from utils.formats import rawfile


def gutenberg_richter(b=1.0, size=None, m_min=2.0, m_max=None):
    """
    """
    if m_max:
        bound_term = 1.0 - 10 ** (-b * (m_max - m_min))
    else:
        bound_term = 1.0
    return m_min - np.log10(-np.random.rand(size) * bound_term + 1.0) / b


def generate_artificial_earthquake(tmax, t0, fs, P_signal_db, P_noise_db,
                                   bfirls, low_period=50., high_period=10.,
                                   bandwidth=4., overlap=1., f_low=2.,
                                   f_high=18., low_amp=.2, high_amp=.1):
    """
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
    """
    """
    L = tmax * fs
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
                              f_filt_high[i] / (fs / 2.)])
        noise_band[i, :] = signal.lfilter(b, a, w_noise)
    # First earthquake sample
    n0 = round(t0 * L / tmax)
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
        noise_env[i, n0:n1[i]] = (filt_amp[i] *
                                   np.exp(-alpha[i] *
                                          (np.arange(n0, n1[i]) - n0)))
    # We multiply the envelope for each noise band
    noise_band_envelope = noise_band * noise_env
    artificial_earthquake = np.sum(noise_band_envelope, 0)
    eq_pw_db = 10 * np.log10(np.var(artificial_earthquake[n0:n0 + 5 * fs]))
    # We want the earthquake has a power in dB given by P_signal_db
    gamma_signal = 10 ** ((P_signal_db - eq_pw_db) / 20)
    artificial_earthquake = gamma_signal * artificial_earthquake
    return artificial_earthquake


def generate_seismic_noise(tmax, fs, P_noise_db, bfirls):
    """
    """
    L = tmax * fs
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
    """
    """

    def __init__(self, bfirls=np.array([1]), fs=50.0, P_noise_db=0.0,
                 low_period=50.0, high_period=10.0, bandwidth=4.0,
                 overlap=1.0, f_low=2.0, f_high=18.0,
                 low_amp=0.2, high_amp=0.1, **kwargs):
        """"""
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

    def load_noise_coefficients(self, fileobj, dtype, byteorder):
        """"""
        fhandler = rawfile.get_file_handler(fileobj, dtype=dtype,
                                            byteorder=byteorder)
        self.bfirls = fhandler.read()

    def generate_events(self, t_average, t_max, b=1.0,
                               m_min=2.0, m_max=7.0):
        """"""
        event_t = []
        t = np.random.poisson(t_average)
        while t < t_max:
            event_t.append(t)
            t += np.random.poisson(t_average)
        event_m = gutenberg_richter(b, len(event_t), m_min, m_max)
        return np.array(event_t), event_m

    def generate_nevents(self, t_average, event_n, b=1.0,
                               m_min=2.0, m_max=7.0):
        """"""
        event_t = np.cumsum(np.random.poisson(t_average, event_n))
        event_m = gutenberg_richter(b, event_n, m_min, m_max)
        return event_t, event_m

    def generate_sequence(self, t_max, event_t, event_m):
        event_n = len(event_t)
        """"""
        out = generate_seismic_noise(t_max, self.fs, self.P_noise_db,
                                     self.bfirls)

        eq_len = max(self.low_period, self.high_period)
        for i in xrange(event_n):
            size = min(eq_len, t_max - event_t[i])
            eq = generate_seismic_earthquake(eq_len, 0.,
                                             self.fs, event_m[i],
                                             self.low_period, self.high_period,
                                             self.bandwidth, self.overlap,
                                             self.f_low, self.f_high,
                                             self.low_amp, self.high_amp)
            i_from = int(event_t[i] * self.fs)
            i_to = int((event_t[i] + size) * self.fs)
            out[i_from:i_to] += eq[:size * self.fs]

        return out

    def generate_earthquake(self, t_max, t0, p_eq, eq=None):
        """"""
        if eq == None:
            return generate_artificial_earthquake(t_max, t0, self.fs, p_eq,
                                                  self.P_noise_db, self.bfirls,
                                                  self.low_period,
                                                  self.high_period,
                                                  self.bandwidth, self.overlap,
                                                  self.f_low, self.f_high,
                                                  self.low_amp, self.high_amp)
        else:
            out = generate_seismic_noise(t_max, self.fs, self.P_noise_db,
                                         self.bfirls)
            size = int(min(len(eq), (t_max - t0) * self.fs))
            i_from = int(t0 * self.fs)
            i_to = int(t0 * self.fs + size)
            out[i_from:i_to] += eq[:size]
            return out
