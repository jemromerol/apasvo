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

from picking import findpeaks
from numpy.lib import stride_tricks


def sta_lta(x, fs, threshold=None, sta_length=5., lta_length=100.,
            peak_window=1.):
    """Event picking/detection using STA-LTA algorithm.

    The STA-LTA algorithm processes seismic signals by using two moving time
    windows, a short time average window (STA), which measures the instant
    amplitude of the signal and watches for earthquakes, and a long time
    average windows, which takes care of the current average of the signal
    amplitude.

    See:
    Trnkoczy, A. (2002). Understanding and parameter setting of STA/LTA trigger
    algorithm. IASPEI New Manual of Seismological Observatory Practice, 2, 1-19.

    Args:
        x: Seismic data, numpy array type.
        fs: Sampling rate in Hz.
        threshold: Local maxima found in the characteristic function over
            this value will be returned by the function as possible events
            (detection mode).
            If threshold is None, the function will return only the global
            maximum (picking mode).
            Default value is None.
        sta_length: Length of STA window, in seconds.
            Default: 5.0 seconds.
        lta_length: Length of LTA window, in seconds:
            Default: 100.0 seconds.
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
        cf: Characteristic function, numpy array type.
    """
    # Check arguments
    if fs <= 0:
        raise ValueError("fs must be a positive value")
    if fs != int(fs):
        raise ValueError("fs must be an integer value")
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
    # FASTER VERSION USING STRIDES
    if len(cf) > 0:
        sta_win = stride_tricks.as_strided(x_norm, shape=(len(x_norm) - lta + 1, sta),
                                           strides=(1 * x_norm.dtype.itemsize, 1 * x_norm.dtype.itemsize))
        lta_win = stride_tricks.as_strided(x_norm, shape=(len(x_norm) - lta + 1, lta),
                                           strides=(1 * x_norm.dtype.itemsize, 1 * x_norm.dtype.itemsize))
        cf[:len(x_norm) - lta + 1] = sta_win.mean(axis=1) / lta_win.mean(axis=1)
#     for i in xrange(len(x_norm)):
#         sta_to = int(min(len(x_norm), i + sta))
#         lta_to = int(min(len(x_norm), i + lta))
#         cf[i] = np.mean(x_norm[i:sta_to]) / np.mean(x_norm[i:lta_to])
    event_t = findpeaks.find_peaks(cf, threshold, order=peak_window * fs)
    return event_t, cf


class StaLta(object):
    """A class to configure an instance of the STA-LTA algorithm and
    apply it over a given seismic signal.

    Attributes:
        sta_length: Length of STA window, in seconds.
            Default: 5.0 seconds.
        lta_length: length of LTA window, in seconds.
            Default 100.0 seconds.
    """

    def __init__(self, sta_length=5.0, lta_length=100.0, **kwargs):
        super(StaLta, self).__init__()
        self.sta_length = sta_length
        self.lta_length = lta_length

    def run(self, x, fs, threshold=None, peak_window=1.0):
        """Executes STA-LTA algorithm over a given array of data

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
            cf: Characteristic function, numpy array type.
        """
        et, cf = sta_lta(x, fs, threshold=threshold,
                         sta_length=self.sta_length,
                         lta_length=self.lta_length,
                         peak_window=peak_window)
        return et, cf
