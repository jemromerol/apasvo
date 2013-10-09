'''
Created on 23/05/2013

@author: Jose Emilio Romero Lopez
'''

import numpy as np
from scipy import signal
import utils
import csv
import os
import matplotlib.pyplot as pl
from matplotlib.ticker import FuncFormatter
import datetime
import collections


def prctile(x, p):
    # Check range of p values
    if isinstance(p, collections.Iterable):
        iterable = True
        for v in p:
            if v < 0 or v > 100:
                raise ValueError("p should be in range [0, 100]")
    else:
        iterable = False
        if p < 0 or p > 100:
            raise ValueError("p should be in range [0, 100]")
    # If x is empty return all NaNs
    if len(x) == 0:
        if iterable:
            return np.empty(len(p)) * np.nan
        return np.nan
    sorted_x = np.sort(x)
    # If p == 50 make the median fast
    if p == 50:
        return np.median(sorted_x)
    q = np.hstack([0, 100 * np.linspace(0.5, len(x) - 0.5, len(x)) / len(x), 100])
    xx = np.hstack([sorted_x[0], sorted_x, sorted_x[-1]])
    return np.interp(p, q, xx)


def envelope(x):
    return np.abs(signal.hilbert(x))


def find_peaks(x, threshold=None, order=1):
    if threshold is not None:
        event_peaks = signal.argrelmax(x, order=int(order))[0]
        if event_peaks.size > 0:
            return event_peaks[x[event_peaks] > threshold]
        return event_peaks
    else:
        if x.size > 0:
            return np.array([np.argmax(x)])
        return np.array([])


def sta_lta(x, fs, threshold=None, sta_length=5., lta_length=100.,
            peak_window=1.):
    # Check arguments
    if fs <= 0:
        raise ValueError("fs must be a positive value")
    if sta_length <= 0:
        raise ValueError("sta_length must be a positive value")
    if lta_length <= 0:
        raise ValueError("lta_length must be a positive value")
    if sta_length >= lta_length:
        raise ValueError("lta_length must be greater than sta_length")
    sta = sta_length * fs
    lta = lta_length * fs
    peak_window = int(peak_window * fs / 2.)
    x_norm = np.abs(x - np.mean(x))
    cf = np.zeros(len(x))
    for i in xrange(len(x_norm)):
        sta_to = int(min(len(x_norm), i + sta + 1))
        lta_to = int(min(len(x_norm), i + lta + 1))
        cf[i] = np.mean(x_norm[i:sta_to]) / np.mean(x_norm[i:lta_to])
    event_t = find_peaks(cf, threshold, order=peak_window * fs)
    return event_t, cf


def ampa(x, fs, threshold=None, L=[30., 20., 10., 5., 2.5], L_coef=3.,
         noise_thr=90, bandwidth=3., overlap=1., f_start=2., max_f_end=12.,
         U=12., peak_window=1.):
    # Check arguments
    if fs <= 0:
        raise ValueError("fs must be a positive value")
    if bandwidth <= 0:
        raise ValueError("bandwidth must be a positive value")
    if overlap < 0:
        raise ValueError("overlap must be a non-negative value")
    if overlap >= bandwidth:
        raise ValueError("bandwidth must be greater than overlap")
    if f_start <= 0:
        raise ValueError("f_start must be a positive value")
    if max_f_end <= 0:
        raise ValueError("max_f_end must be a positive value")
    if f_start >= max_f_end:
        raise ValueError("max_f_end must be greater than f_start")
    if U <= 0:
        raise ValueError("U must be a positive value")
    if not isinstance(L, collections.Iterable):
        L = [L]
    for v in L:
        if v <= 0:
            raise ValueError("L should be a positive value")
        if v >= len(x) / fs:
            raise ValueError("Length of x must be greater than the longest of the values of L")
    fs = float(fs)
    peak_window = round(peak_window * fs / 2.)
    t = np.arange(0, len(x) / fs, 1. / fs)
    x = x - np.mean(x)  # We remove the mean
    # The first configurable parameter is the bank of bandpass filters
    # Several options can be chosen
    f_end = min(fs / 2. - bandwidth, max_f_end)
    if f_end <= f_start:
        raise ValueError("The end frequency of the filter bank must be greater than its start frequency")
    step = bandwidth - overlap
    flo = np.arange(f_start, f_end + step, step)
    fhi = flo + bandwidth
    # We obtain the analytic signal using Hilbert transform
    z = np.zeros((len(flo), len(x)))
    for i in xrange(len(flo)):
        h_aux = 8 - (np.arange(32) / 4.)
        h0 = np.zeros(512)
        h0[0:32] = h_aux * np.cos(2. * np.pi * ((flo[i] + fhi[i]) / 2.) *
                                  np.arange(32) / fs)
        h0o = np.imag(signal.hilbert(h0))
        # Filtering the signal
        xa = np.convolve(x, h0)[:len(x)]  # Same as signal.lfilter(h0, 1, x)
        xao = np.convolve(x, h0o)[:len(x)]  # Same as signal.lfilter(h0o, 1, x)
        # Analytic signal
        y0 = np.sqrt((xa ** 2) + (xao ** 2))
        # Fix a threshold to modify the energies in the channels
        thr = prctile(y0, noise_thr)
        # Here we modify the amplitudes of the analytic signal. The amplitudes
        # below the threshold are set to 1. the amplitudes above the threshold
        # are set to the number of times they are higher than the threshold
        z0 = (y0 / thr) * (y0 > thr) + (y0 <= thr)
        # In the variable z we save the analytic signals (modified by the
        # threshold processing) in a matrix structure. Each column corresponds
        # to one frequency channel
        z[i, :] = z0
    # We sum the contribution of all the frequency channels in a single signal
    # Then we apply logarithm
    ztot = np.sum(z, 0)
    lztot = np.log10(ztot) - np.min(np.log10(ztot)) + 1e-2
    # This total signal is passed through a non-linear filtering based
    # on a set of filters of different length. This is completely configurable
    Ztot = np.zeros((len(L), len(t)))
    for i in xrange(len(L)):
        l = int(L[i] * fs)
        B = np.zeros(2 * l)
        B[0:l] = range(1, l + 1)
        B[l:2 * l] = L_coef * (np.arange(1, l + 1) - (l + 1))
        B = B / np.sum(np.abs(B))
        Zt = np.convolve(lztot, B)[:len(x)]  # Same as signal.lfilter(B, 1, lztot)
        Zt = Zt * (Zt > 0)
        Ztot[i, :-l] = np.roll(Zt, -l)[:-l]
    ZTOT = np.prod(Ztot, 0)[:-(np.max(L) * fs)]
    ZTOT = U + np.log10(np.abs(ZTOT) + (10 ** -U))
    event_t = find_peaks(ZTOT, threshold, order=peak_window * fs)
    return event_t, ZTOT


def takanami(x, n0, n1, p=1, k=5):
    l = (n1 - n0) / float(p)  # l + 1 models
    # Noise Model
    noise_aic = takanami_aic(x, n0, l, k, p)
    # Earthquake Model
    # Invert the signal, so the procedure is similar to the noise model's one
    x = x[::-1]
    new_n0 = len(x) - (n1 + 1) + 1  # n0's value changes
    earthquake_aic = takanami_aic(x, new_n0, l, k, p)
    earthquake_aic = earthquake_aic[::-1]
    # Picking time estimation
    total_aic = noise_aic + earthquake_aic
    event_idx = np.argmin(total_aic)
    n_pick = n0 + (event_idx * p)  # When event_idx = 0 --> n_pick = n0 + 1
    return n_pick, total_aic


def takanami_aic(x, n0, l, k=5, p=1):
    if p <= 0:
        raise ValueError("p should be a positive value")
    if k <= 0:
        raise ValueError("k should be a positive value")
    if n0 <= k:
        raise ValueError("n0 should be greater than k")
    if l <= 0:
        raise ValueError("l should be a positive value")
    aic_0_l = np.zeros(l + 1)
    sigma2 = np.zeros(k + 1)
    aic_i = np.zeros(k + 1)
    # Calculate AIC value for n0
    x_n0 = x[:n0]
    # Initialize X0 matrix
    X0 = np.zeros((n0 - k, k + 1))
    for i in xrange(k):
        X0[:, i] = x_n0[k - i - 1:-1 - i]
    X0[:, k] = x_n0[k:]
    # Householder transformation by QR decomposition
    R0 = np.linalg.qr(X0, mode='r')
    R0 = R0[:k + 1, :k + 1]
    # Calculate variances and AIC...
    c1 = 1. / (n0 - k)
    c2 = n0 - k
    for j in xrange(k + 1):
        sigma2[j] = c1 * np.sum(R0[j:k + 1, k] ** 2)
        aic_i[j] = c2 * np.log(sigma2[j]) + 2 * (j + 1)
    aic_0_l[0] = np.min(aic_i)
    # Calculate AIC from n_1 to n_l
    R = np.zeros((k + 1 + p, k + 1))
    S = R0
    for i in xrange(1, int(l + 1)):
        aug_data = x[(n0 + i * p - k - 1):(n0 + i * p)]  # Augmented Data
        R[:k + 1, :k + 1] = S
        R[k + 1:k + 1 + p, :k] = aug_data[-2::-1]
        R[k + 1:k + 1 + p, k] = aug_data[-1]
        # QR decomposition
        S = np.linalg.qr(R, mode='r')
        S = S[:k + 1, :k + 1]
        # Calculate variances and AIC...
        c1 = 1. / (n0 + i * p - k)
        c2 = n0 + i * p - k
        for j in xrange(k + 1):
            sigma2[j] = c1 * np.sum(S[j:k + 1, k] ** 2)
            aic_i[j] = c2 * np.log(sigma2[j]) + 2 * (j + 1)
        aic_0_l[i] = np.min(aic_i)
    return aic_0_l


def gutenberg_richter(b=1.0, size=None, m_min=2.0, m_max=None):
    if m_max:
        bound_term = 1.0 - 10 ** (-b * (m_max - m_min))
    else:
        bound_term = 1.0
    return m_min - np.log10(-np.random.rand(size) * bound_term + 1.0) / b


def generate_artificial_earthquake(tmax, t0, fs, P_signal_db, P_noise_db,
                                   bfirls, low_period=50., high_period=10.,
                                   bandwidth=4., overlap=1., f_low=2.,
                                   f_high=18., low_amp=.2, high_amp=.1):
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


class StaLta(object):

    def __init__(self, sta_length=10.0, lta_length=600.0, **kwargs):
        super(StaLta, self).__init__()
        self.sta_length = sta_length
        self.lta_length = lta_length
        self.name = 'STA-LTA'

    def run(self, x, fs, threshold=None, peak_window=1.0):
        et, cf = sta_lta(x, fs, threshold=threshold,
                         sta_length=self.sta_length,
                         lta_length=self.lta_length,
                         peak_window=peak_window)
        return et, cf


class Ampa(object):

    def __init__(self, window=100., window_overlap=0.5,
                 L=[30., 20., 10., 5., 2.5], L_coef=3., noise_thr=90.,
                 bandwidth=3., overlap=1., f_start=2.,
                 f_end=12., U=12., **kwargs):
        super(Ampa, self).__init__()
        self.window = window
        self.window_overlap = window_overlap
        self.L = L
        self.L_coef = L_coef
        self.noise_thr = noise_thr
        self.bandwidth = bandwidth
        self.overlap = overlap
        self.f_start = f_start
        self.max_f_end = f_end
        self.U = U
        self.name = 'AMPA'

    def run(self, x, fs, threshold=None, peak_window=1.0):
        tail = int(np.max(self.L) * fs)
        out = np.zeros(len(x) - tail)
        step = int(self.window * (1. - self.window_overlap) * fs)
        overlapped = max(0, int(self.window * self.window_overlap * fs) - tail)
        for i in xrange(0, len(out), step):
            size = min(self.window * fs, len(x) - i)
            _, cf = ampa(x[i:i + size], fs, L=self.L,
                         L_coef=self.L_coef, noise_thr=self.noise_thr,
                         bandwidth=self.bandwidth, overlap=self.overlap,
                         f_start=self.f_start, max_f_end=self.max_f_end,
                         U=self.U)
            out[i: i + overlapped] = ((out[i: i + overlapped] +
                                       cf[:overlapped]) / 2.)
            out[i + overlapped: i + size - tail] = cf[overlapped:]
        et = find_peaks(out, threshold, order=peak_window * fs)
        return et, out


class Takanami(object):

    def __init__(self, p=1, k=5):
        super(Takanami, self).__init__()
        self.p = p
        self.k = k

    def run(self, x, fs, t_start=0.0, t_end=np.inf):
        i_from = int(max(0, t_start * fs))
        i_to = int(min(len(x), t_end * fs))
        n0 = (self.k + 1) * 2
        n1 = (i_to - i_from) - n0
        pt, aic = takanami(x[i_from:i_to], n0, n1, p=self.p, k=self.k)
        return i_from + pt, aic, i_from + n0


class EarthquakeGenerator(object):

    def __init__(self, bfirls=np.array([1]), fs=50.0, P_noise_db=0.0,
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

    def load_noise_coefficients(self, file, dtype, byteorder):
        fhandler = utils.get_file_handler(file, dtype=dtype, byteorder=byteorder)
        self.bfirls = fhandler.read()

    def generate_events(self, t_average, t_max, b=1.0,
                               m_min=2.0, m_max=7.0):
        event_t = []
        t = np.random.poisson(t_average)
        while t < t_max:
            event_t.append(t)
            t += np.random.poisson(t_average)
        event_m = gutenberg_richter(b, len(event_t), m_min, m_max)
        return np.array(event_t), event_m

    def generate_nevents(self, t_average, event_n, b=1.0,
                               m_min=2.0, m_max=7.0):
        event_t = np.cumsum(np.random.poisson(t_average, event_n))
        event_m = gutenberg_richter(b, event_n, m_min, m_max)
        return event_t, event_m

    def generate_sequence(self, t_max, event_t, event_m):
        event_n = len(event_t)

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
        if eq == None:
            return generate_artificial_earthquake(t_max, t0, self.fs, p_eq,
                                                  self.P_noise_db, self.bfirls,
                                                  self.low_period, self.high_period,
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


class Event(object):

    methods = ['other', 'STA-LTA', 'STA-LTA+Takanami', 'AMPA', 'AMPA+Takanami']
    modes = ['manual', 'automatic', 'undefined']
    states = ['reported', 'revised', 'confirmed', 'rejected', 'undefined']

    def __init__(self, time, cf_value, name='', comments='', method='other',
                 mode='automatic', state='reported', aic=None, n0_aic=None, **kwargs):
        super(Event, self).__init__()
        self.time = time
        self.cf_value = cf_value
        self.name = name
        self.comments = comments
        self.method = method
        if mode not in self.modes:
            mode = 'undefined'
        self.mode = mode
        if state not in self.states:
            state = 'undefined'
        self.state = state
        self.aic = aic
        self.n0_aic = n0_aic


class Record(object):

    def __init__(self, fileobj, fs, label='', description='', fmt='', dtype='float64', byteorder='native', **kwargs):
        super(Record, self).__init__()
        if isinstance(fileobj, file):
            self.filename = fileobj.name
        else:
            self.filename = fileobj
        fhandler = utils.get_file_handler(fileobj, fmt=fmt, dtype=dtype, byteorder=byteorder)
        self.signal = fhandler.read()
        self.fs = fs
        self.cf = np.array([])
        self.events = []
        if label == '':
            _, rname = os.path.split(self.filename)
            label, _ = os.path.splitext(rname)
        self.label = label
        self.description = description

    def detect(self, alg, threshold=None, peak_checking=1.0, sort='vd',
               takanami=False, takanami_margin=5.0, **kwargs):
        et, self.cf = alg.run(self.signal, self.fs, threshold=threshold,
                                peak_window=peak_checking)
        # Build event list
        self.events = []
        for t in et:
            self.events.append(Event(t / self.fs, self.cf[t], method=alg.name,
                                     mode='automatic', state='reported'))
        # Sort results
        key = 'cf_value' if sort[0] == 'v' else 'time'
        reverse = True if sort[1] == 'd' else False
        self.sort_events(key, reverse)
        # Refine
        if takanami:
            self._refine_events(takanami_margin)
        return self.events

    def sort_events(self, key='time', reverse=False):
        if key == 'aic':
            raise ValueError("Sorting not allowed using key 'aic'")
        self.events = sorted(self.events, key=lambda e: e.__dict__.get(key, None), reverse=reverse)

    def _refine_events(self, takanami_margin=5.0):
        taka = Takanami()
        for event in self.events:
            t_start = event.time - takanami_margin
            t_end = event.time + takanami_margin
            et, event.aic, event.n0_aic = taka.run(self.signal, self.fs,
                                                   t_start, t_end)
            event.time = et / self.fs
            event.cf_value = self.cf[et]
        return self.events

    def save_cf(self, fname, fmt='binary', dtype='float64', byteorder='native'):
        fout_handler = utils.TextFile(fname, dtype=dtype, byteorder=byteorder) if fmt == 'text' else utils.BinFile(fname, dtype=dtype, byteorder=byteorder)
        fout_handler.write(self.cf)

    def plot_signal(self, t_start=0.0, t_end=np.inf, show_events=True,
                    show_x=True, show_cf=True, show_specgram=True,
                    show_envelope=True, threshold=None, num=None, **kwargs):
        # Set limits
        i_from = int(max(0.0, t_start * self.fs))
        if show_cf:
            i_to = int(min(len(self.cf), t_end * self.fs))
        else:
            i_to = int(min(len(self.signal), t_end * self.fs))
        # Create time sequence
        t = np.arange(i_from, i_to) / self.fs
        # Create figure
        nplots = show_x + show_cf + show_specgram
        fig, _ = pl.subplots(nplots, 1, sharex='all', num=num)
        fig.canvas.set_window_title(self.label)
        fig.set_tight_layout(True)
        # Configure axes
        for ax in fig.axes:
            ax.cla()
            ax.grid(True, which='both')
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f' % x))
            ax.set_xlabel('Time (seconds)')
            pl.setp(ax.get_xticklabels(), visible=True)
        # Draw axes
        ax_idx = 0
        # Draw signal
        if show_x:
            fig.axes[ax_idx].set_title("Signal Amplitude (%gHz)" % self.fs)
            fig.axes[ax_idx].set_ylabel('Amplitude')
            fig.axes[ax_idx].plot(t, self.signal[i_from:i_to], color='b', label='Signal')
            # Draw signal envelope
            if show_envelope:
                fig.axes[ax_idx].plot(t, envelope(self.signal[i_from:i_to]),
                                  color='g', label='Envelope')
                fig.axes[ax_idx].legend(loc=0, fontsize='small')
            ax_idx += 1
        # Draw Characteristic function
        if show_cf:
            fig.axes[ax_idx].set_title('Characteristic Function')
            fig.axes[ax_idx].plot(t, self.cf[i_from:i_to])
            # Draw threshold
            if threshold:
                hline = fig.axes[ax_idx].axhline(threshold, label="Threshold")
                hline.set(color='b', ls='--', lw=2, alpha=0.8)
                fig.axes[ax_idx].legend(loc=0, fontsize='small')
            ax_idx += 1
        # Draw spectrogram
        if show_specgram:
            fig.axes[ax_idx].set_title('Spectrogram')
            fig.axes[ax_idx].set_ylabel('Frequency (Hz)')
            fig.axes[ax_idx].specgram(self.signal[i_from:i_to], Fs=self.fs,
                                  xextent=(i_from / self.fs, i_to / self.fs))
            ax_idx += 1
        # Draw event markers
        if show_events:
            for event in self.events:
                for ax in fig.axes:
                    xmin, xmax = ax.get_xlim()
                    if event.time > xmin and event.time < xmax:
                        vline = ax.axvline(event.time, label="Event")
                        vline.set(color='r', ls='--', lw=2)
                        ax.legend(loc=0, fontsize='small')
        # Configure limits and draw legend
        for ax in fig.axes:
            ax.set_xlim(t[0], t[-1])
        return fig

    def plot_aic(self, event, show_envelope=True, num=None, **kwargs):
        # Set limits
        i_from = int(max(0, event.n0_aic))
        i_to = int(min(len(self.signal), event.n0_aic + len(event.aic)))
        # Create time sequence
        t = np.arange(i_from, i_to) / self.fs
        # Create figure
        fig, _ = pl.subplots(2, 1, sharex='all', num=num)
        fig.canvas.set_window_title(self.label)
        fig.set_tight_layout(True)
        # Configure axes
        for ax in fig.axes:
            ax.cla()
            ax.grid(True, which='both')
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f' % x))
            ax.set_xlabel('Time (seconds)')
            pl.setp(ax.get_xticklabels(), visible=True)
        # Draw signal
        fig.axes[0].set_title('Signal Amplitude')
        fig.axes[0].set_ylabel('Amplitude')
        fig.axes[0].plot(t, self.signal[i_from:i_to], color='b', label='Signal')
        # Draw envelope
        if show_envelope:
            fig.axes[0].plot(t, envelope(self.signal[i_from:i_to]),
                         color='g', label='Envelope')
            fig.axes[0].legend(loc=0, fontsize='small')
        # Draw AIC
        fig.axes[1].set_title('AIC')
        fig.axes[1].plot(t, event.aic)
        # Draw event
        for ax in fig.axes:
            vline = ax.axvline(event.time, label="Event")
            vline.set(color='r', ls='--', lw=2)
        # Configure limits and draw legend
        for ax in fig.axes:
            ax.set_xlim(t[0], t[-1])
            ax.legend(loc=0, fontsize='small')
        return fig


class RecordFactory(object):

    def __init__(self, max_segment_length=24*7*3600, fs=50.0, dtype='float64', byteorder='native',
                 notif=None, **kwargs):
        self.fs = fs
        self.dtype = dtype
        self.byteorder = byteorder
        self.max_record_length = (max_segment_length * fs)
        self.notif = notif

    def create_record(self, fileobj, **kwargs):
#         segment_n = np.ceil(utils.getSize(fileobj) / self.max_record_length)
#         if segment_n > 1:
#             fhandler = utils.get_file_handler(fileobj, dtype=self.dtype, byteorder=self.byteorder)
#             self.on_notify("File %s is too long, it will be divided into %i parts up to %g seconds each\n"
#                            % (fhandler.filename, segment_n, self.max_record_length / self.fs))
#             basename, ext = os.path.splitext(fhandler.filename)
#             fileno = 0
#             records = []
#             for segment in fhandler.read_in_blocks(self.max_record_length):
#                 filename_out = "%s%02.0i%s" % (basename, fileno, ext)
#                 fout_handler = utils.TextFile(filename_out, self.dtype, self.byteorder) if isinstance(fhandler, utils.TextFile) else utils.BinFile(filename_out, self.dtype, self.byteorder)
#                 fileno += 1
#                 fout_handler.write(segment)
#                 self.on_notify("%s generated.\n" % fout_handler.filename)
#                 records.append(fout_handler.filename, self.fs,
#                                       dtype=self.dtype, byteorder=self.byteorder,
#                                       **kwargs)
#             return records
#         else:
        return Record(fileobj, self.fs, dtype=self.dtype, byteorder=self.byteorder,
                      **kwargs)

    def on_notify(self, msg):
        pass


def generate_csv(records, out, delimiter='\t', lineterminator='\n'):
    # Extract data from records
    rows = [{'file_name': record.filename,
             'time': str(datetime.timedelta(seconds=event.time)),
             'cf_value': event.cf_value,
             'name': event.name,
             'method': event.method,
             'mode': event.mode,
             'state': event.state,
             'comments': event.comments} for record in records
                                         for event in record.events]
    # Write data to csv
    writer = csv.DictWriter(out, ['file_name', 'time', 'cf_value', 'name', 'method', 'mode', 'state', 'comments'],
                            delimiter=delimiter, lineterminator=lineterminator)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

