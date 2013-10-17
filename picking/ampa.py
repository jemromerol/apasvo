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
import collections

from picking import findpeaks


def prctile(x, p):
    """
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
    """
    """
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
    t = np.arange(0, len(x) / fs, 1. / fs)
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
    event_t = findpeaks.find_peaks(ZTOT, threshold, order=peak_window * fs)
    return event_t, ZTOT


class Ampa(object):
    """
    """

    def __init__(self, window=100., window_overlap=0.5,
                 L=None, L_coef=3., noise_thr=90.,
                 bandwidth=3., overlap=1., f_start=2.,
                 f_end=12., U=12., **kwargs):
        """"""
        super(Ampa, self).__init__()
        self.window = window
        self.window_overlap = window_overlap
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
        self.name = 'AMPA'

    def run(self, x, fs, threshold=None, peak_window=1.0):
        """"""
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
        et = findpeaks.find_peaks(out, threshold, order=peak_window * fs)
        return et, out
