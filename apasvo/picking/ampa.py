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
import collections

from apasvo.picking import findpeaks


def prctile(x, p):
    """Computes a percentile of a vector.

    MATLAB like implementation of the percentile algorithm.

    Args:
        x: An unidimensional data array.
        p: A percentage in the range [0,100].

    Returns:
        If 'x' is not empty returns the 'p' percentile of x,
        else returns nan.
    """
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
    q = np.hstack([0,
                   100 * np.linspace(0.5, len(x) - 0.5, len(x)) / len(x),
                   100])
    xx = np.hstack([sorted_x[0], sorted_x, sorted_x[-1]])
    return np.interp(p, q, xx)


def ampa(x, fs, threshold=None, L=None, L_coef=3.,
         noise_thr=90, bandwidth=3., overlap=1., f_start=2., max_f_end=12.,
         U=12., peak_window=1.):
    """Event picking/detection using AMPA algorithm.

    An implementation of the Adaptive Multi-Band Picking Algorithm (AMPA),
    as described in:

    Álvarez, I., García, L., Mota, S., Cortés, G., Benítez, C.,
    & De la Torre, A. (2013).
    An Automatic P-Phase Picking Algorithm Based on Adaptive Multiband Processing.
    Geoscience and Remote Sensing Letters, IEEE,
    Volume: 10, Issue: 6, pp. 1488 - 1492

    The AMPA method consists on an adaptive multi-band analysis that includes
    envelope detection, noise reduction for each band, and finally a
    filter stage that enhances the response to an earthquake arrival.
    This approach provides accurate estimation of phase arrivals in
    seismic signals strongly affected by background and non-stationary noises.

    Args:
        x: Seismic data, numpy array type.
        fs: Sampling rate in Hz.
        threshold: Local maxima found in the characteristic function over
            this value will be returned by the function as possible events
            (detection mode).
            If threshold is None, the function will return only the global
            maximum (picking mode).
            Default value is None.
        L: A list of filter lengths (in seconds).
            At the filter stage, the signal is processed by using a set of
            enhancement filters of different length L=[l1, l2, ..., ln].
            The length of a filter is related to the duration of the detected
            events. An enhancement filter for long duration events can negate
            short duration events and vice versa. Combining several filters of
            different length the algorithm achieves to deal with this issue.
            Default: [30.0, 20.0, 10.0, 5.0, 2.5]
        L_coef: A parameter that measures the portion of negative response of
            an enhancement filter in order to minimize the response to emerging
            or impulsive noises.
            Default value is 3.0.
        noise_thr: A percentile of the amplitude of the envelope that measures
            the noise reduction level for each band at the noise reduction
            stage.
            Default value is 90.
        bandwidth: Bandwidth of each band at the adaptive multi-band analysis.
            Default: 3 Hz.
        overlap: Overlap between bands at the adaptive multi-band analysis.
            Default: 1 Hz.
        f_start: Start frequency at the adaptive multi-band analysis.
            Default: 2 Hz.
        max_f_end: End frequency at the adaptive multi-band analysis.
            Default: 12 Hz.
        U: A parameter used at the end of the enhancement filter stage to avoid
            logarithm of zero and to shift the characteristic function to zero.
            Given y(n) the product of the outputs of the different filters used
            at the end of the enhancement stage, the characteristic function is
            then calculated as:

                cf(n) = U + log10(y(n) + 10 ** (-U))

            Default value is 12.
        peak_window: How many seconds on each side of a point of the
            characteristic function to use for the comparison to consider the
            point to be a local maximum.
            If 'threshold' is None, this parameter has no effect.
            Default value is 1 s.

    Returns:
        event_t: A list of possible event locations, given in samples from the
            start of the signal, that correspond to the local maxima of the
            characteristic function. If threshold is None, the list contains
            only the global maximum of the function.
        ztot: Characteristic function, numpy array type.
    """
    # Check arguments
    if fs <= 0:
        raise ValueError("fs must be a positive value")
    if fs != int(fs):
        raise ValueError("fs must be an integer value")
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
    if L is None:
        L = [30., 20., 10., 5., 2.5]
    for v in L:
        if v <= 0:
            raise ValueError("L should be a positive value")
        if v >= len(x) / fs:
            raise ValueError("Length of x must be greater than the longest "
                             "of the values of L")
    fs = float(fs)
    peak_window = round(peak_window * fs / 2.)
    x = x - np.mean(x)  # We remove the mean
    # The first configurable parameter is the bank of bandpass filters
    # Several options can be chosen
    f_end = min(fs / 2. - bandwidth, max_f_end)
    if f_end <= f_start:
        raise ValueError("The end frequency of the filter bank must be greater"
                         " than its start frequency")
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
        xa = signal.fftconvolve(x, h0)[:len(x)]  # Same as signal.lfilter(h0, 1, x)
        xao = signal.fftconvolve(x, h0o)[:len(x)]  # Same as signal.lfilter(h0o, 1, x)
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
    Ztot = np.zeros((len(L), len(x)))
    for i in xrange(len(L)):
        l = int(L[i] * fs)
        B = np.zeros(2 * l)
        B[0:l] = range(1, l + 1)
        B[l:2 * l] = L_coef * (np.arange(1, l + 1) - (l + 1))
        B = B / np.sum(np.abs(B))
        Zt = signal.fftconvolve(lztot, B)[:len(x)]  # Same as signal.lfilter(B, 1, lztot)
        Zt = Zt * (Zt > 0)
        Ztot[i, :-l] = np.roll(Zt, -l)[:-l]
    ZTOT = np.prod(Ztot, 0)[:-(np.max(L) * fs)]
    ZTOT = U + np.log10(np.abs(ZTOT) + (10 ** -U))
    event_t = findpeaks.find_peaks(ZTOT, threshold, order=peak_window * fs)
    return event_t, ZTOT


class Ampa(object):
    """A class to configure an instance of the AMPA algorithm and
    apply it over a given array containing seismic data.

    Given some overlap and window sizes, this class applies the AMPA method
    by using a sliding window approach.

    Attributes:
        window: Size of the window in seconds. Default: 100 seconds.
        step: Step size. Default: 50 seconds.
        L: A list of filter lengths (in seconds) at the enhancement filter
            stage. Default: [30.0, 20.0, 10.0, 5.0, 2.5]
        L_coef: A parameter that measures the portion of negative response of
            an enhancement filter in order to minimize the response to emerging
            or impulsive noises.
            Default value is 3.0.
        noise_thr: A percentile of the amplitude of the envelope that measures
            the noise reduction level for each band at the noise reduction
            stage.
            Default value is 90.
        bandwidth: Bandwidth of each band of the adaptive multi-band analysis.
            Default: 3 Hz.
        overlap: Overlap between bands of the adaptive multi-band analysis.
            Default: 1 Hz.
        f_start: Start frequency of the adaptive multi-band analysis.
            Default: 2 Hz.
        max_f_end: End frequency of the adaptive multi-band analysis.
            Default: 12 Hz.
        U: A parameter used at the end of the enhancement filter stage to avoid
            logarithm of zero and to shift the characteristic function to zero.
            Default value is 12.
    """

    def __init__(self, window=100., step=50.,
                 L=None, L_coef=3., noise_thr=90.,
                 bandwidth=3., overlap=1., f_start=2.,
                 f_end=12., U=12., **kwargs):
        super(Ampa, self).__init__()
        self.window = window
        self.step = step
        self.L = L
        if self.L is None:
            self.L = [30., 20., 10., 5., 2.5]
        self.L_coef = L_coef
        self.noise_thr = noise_thr
        self.bandwidth = bandwidth
        self.overlap = overlap
        self.f_start = f_start
        self.max_f_end = f_end
        self.U = U

    def run(self, x, fs, threshold=None, peak_window=1.0):
        """Executes AMPA algorithm over a given array of data.

        Args:
            x: Seismic data, numpy array type.
            fs: Sample rate in Hz.
            threshold: Local maxima found in the characteristic function over
                this value will be returned by the function as possible events
                (detection mode).
                If threshold is None, the function will return only the global
                maximum (picking mode).
                Default value is None.
            peak_window: How many seconds on each side of a point of the
                characteristic function to use for the comparison to consider
                the point to be a local maximum.
                If 'threshold' is None, this parameter has no effect.
                Default value is 1 s.

        Returns:
            et: A list of possible event locations, given in samples from the
                start of the signal, that correspond to the local maxima of the
                characteristic function. If threshold is None, the list contains
                only the global maximum of the function.
            out: Characteristic function, numpy array type.
        """
        tail = int(np.max(self.L) * fs)
        out = np.zeros(len(x) - tail)
        step = int(self.step * fs)
        overlapped = max(0, int((self.window - self.step) * fs) - tail)
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
        et = findpeaks.find_peaks(out, threshold, order=peak_window * fs)
        return et, out
