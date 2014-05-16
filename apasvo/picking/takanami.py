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


def takanami(x, n0, n1, p=1, k=5):
    """Event picking using Takanami AR algorithm.

    The Takanami algorithm estimates the arrival time of a seismic signal
    by using two autoregressive models: a model that fits the earthquake and
    a noise model. Assuming that the characteristics before and after the
    arrival of the earthquake are quite different, the arrival time is
    estimated by searching the time point where the minimum value of the
    Akaike's Information Criterion is reached.

    See:
    Takanami, T., & Kitagawa, G. (1988).
    A new efficient procedure for the estimation of onset times of seismic
    waves. Journal of Physics of the Earth, 36(6), 267-290.

    Args:
        x: A seismic signal, numpy array type.
        n0: Initial point of the interval [n0,n1] where the method assumes
            the arrival time is in.
            The value is given in samples from the beginning of 'x'.
        n1: Final point of the interval [n0,n1] where the method assumes that
            the arrival time is on it.
            The value is given in samples from the beginning of 'x'.
        p: Step of the autoregressive model.
            Default: 1.
        k: Order of the autoregressive model.
            Default: 5.

    Returns:
        n_pick: Arrival time.
            The value is given in samples from the beginning of 'x'.
        total_aic: List of AIC values from 'n0' to 'n1'
    """
    l = (n1 - n0) / float(p)  # l + 1 models
    # Noise Model
    noise_aic = _takanami_aic(x, n0, l, k, p)
    # Earthquake Model
    # Invert the signal, so the procedure is similar to the noise model's one
    x = x[::-1]
    new_n0 = len(x) - (n1 + 1) + 1  # n0's value changes
    earthquake_aic = _takanami_aic(x, new_n0, l, k, p)
    earthquake_aic = earthquake_aic[::-1]
    # Picking time estimation
    total_aic = noise_aic + earthquake_aic
    event_idx = np.argmin(total_aic)
    n_pick = n0 + (event_idx * p)  # When event_idx = 0 --> n_pick = n0 + 1
    return n_pick, total_aic


def _takanami_aic(x, n0, l, k=5, p=1):
    """Computes AIC values of an autoregressive model.

    Args:
        x: A seismic signal, numpy array type.
        n0: Initial point of the interval [n0,n1] where the method assumes
            the arrival time is in.
            The value is given in samples from the beginning of 'x'.
        l: Number of possible models in the interval [n0,n1].
        k: Order of the autoregressive model.
            Default: 5.
        p: Step of the autoregressive model.
            Default: 1.

    Returns:
        aic_values: List of AIC values from n0 to n1.
    """
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


class Takanami(object):
    """A class to configure an instance of Takanami AR algorithm and
    apply it over a given seismic signal.

    Attributes:
        p: Step of the autoregressive model.
            Default: 1.
        k: Order of the autoregressive model.
            Default: 5.
    """

    def __init__(self, p=1, k=5):
        super(Takanami, self).__init__()
        self.p = p
        self.k = k

    def run(self, x, fs, t_start=0.0, t_end=np.inf):
        """Executes Takanami AR algorithm over a given array of data.

        The function searches an arrival time between two time points 't_start'
        and 't_end'. The Takanami method assumes that the characteristics before
        and after the arrival of the earthquake are quite different, so it's
        important to choose a narrow interval in order to get good results.

        Args:
            x: Seismic data, numpy array type.
            fs: Sample rate in Hz.
            t_start: Start time point of the interval [t_start,t_end] where the
                arrival time is supposed to be.
            t_end: End time point of the interval [t_start, t_end] where the
                arrival time is supposed to be.

        Return:
            et: Arrival time, given in samples from the beginning of 'x'.
            aic: List of AIC values.
            n0: Start time point of 'aic'.
                The value is given in samples from the beginning of 'x'.
        """
        i_from = int(max(0, t_start * fs))
        i_to = int(min(len(x), (t_end * fs) + 1))
        n0 = (self.k + 1) * 2
        n1 = (i_to - i_from) - n0
        pt, aic = takanami(x[i_from:i_to], n0, n1, p=self.p, k=self.k)
        return i_from + pt, aic, i_from + n0

