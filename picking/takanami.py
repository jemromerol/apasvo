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

