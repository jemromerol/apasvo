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

from matplotlib import mlab
from scipy import signal
import numpy as np


SPECGRAM_WINDOWS = ("boxcar", "hamming", "hann", "bartlett",
                            'blackman', "blackmanharris")

SPECGRAM_WINDOWS_NAMES = ("Rectangular", "Hamming", "Hann", "Bartlett",
                          "Blackman", "Blackman-Harris")


def plot_specgram(ax, data, fs, nfft=256, noverlap=128, window='hann',
                  cmap='jet', interpolation='bilinear', rasterized=True):

    if window not in SPECGRAM_WINDOWS:
        raise ValueError("Window not supported")

    elif window == "boxcar":
        mwindow = signal.boxcar(nfft)
    elif window == "hamming":
        mwindow = signal.hamming(nfft)
    elif window == "hann":
        mwindow = signal.hann(nfft)
    elif window == "bartlett":
        mwindow = signal.bartlett(nfft)
    elif window == "blackman":
        mwindow = signal.blackman(nfft)
    elif window == "blackmanharris":
        mwindow = signal.blackmanharris(nfft)

    specgram, freqs, time = mlab.specgram(data, NFFT=nfft, Fs=fs,
                                          window=mwindow,
                                          noverlap=noverlap)
    specgram = 10 * np.log10(specgram[1:, :])
    specgram = np.flipud(specgram)

    freqs = freqs[1:]
    halfbin_time = (time[1] - time[0]) / 2.0
    halfbin_freq = (freqs[1] - freqs[0]) / 2.0
    extent = (time[0] - halfbin_time, time[-1] + halfbin_time,
              freqs[0] - halfbin_freq, freqs[-1] + halfbin_freq)

    ax.imshow(specgram, cmap=cmap, interpolation=interpolation,
                            extent=extent, rasterized=rasterized)
    ax.axis('tight')


def reduce_data(x, y, width, xmin=0, xmax=None):
    """Given x-axis data and y-axis data returns a smaller representation
    of both datasets with a desired length for faster plotting.

    Given a width value, which usually corresponds with the desired pixel width
    of the plot, splits represented x-data range into 'width' partitions and
    returns the (x,y) minimum and maximum data pairs for each partition.

    Args:
        x: x-axis data. Numpy array type.
        y: y-axis data. Numpy array type.
        width: Desired plot width, usually related to plot's pixel width.
        xmin: Position of the first (x,y) data pair to be represented
        xmax: Position of the last (x,y) data pair to be represented
    Returns:
        x_reduced: Reduced x-axis dataset.
        y_reduced: Reduced y-axis dataset.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length.")
    if not isinstance(x, np.ndarray):
        x = np.array(x)
    if not isinstance(y, np.ndarray):
        y = np.array(y)
    # Init xmax and xmin values
    xmax = len(x) - 1 if xmax is None else min(len(x) - 1, xmax)
    xmin = max(0, xmin)
    if not xmin < xmax:
        raise ValueError("xmax must be greater than xmin")
    n_points = 2 * width
    data_size = xmax - xmin

    # If the length of the datasets is too small returns the datasets
    if data_size <= n_points:
        return x[xmin:xmax + 1], y[xmin:xmax + 1]

    indexes = np.empty(n_points + 2, dtype=int)
    # Initial and final (x,y) pairs of the reduced data corresponds
    # with the initial and final (x,y) values of the represented data
    indexes[0], indexes[-1] = xmin, xmax
    i = 1

    limits = np.ceil(np.linspace(xmin, xmax, width + 1)).astype(int)
    for j in xrange(int(width)):
        left = limits[j]
        right = limits[j + 1]
        indexes[i] = left + y[left:right + 1].argmax(axis=0)
        i += 1
        indexes[i] = left + y[left:right + 1].argmin(axis=0)
        i += 1
    indexes.sort()

    return x[indexes], y[indexes]


def adjust_axes_height(ax, margin=0.1):
    max_values = []
    min_values = []
    for line in ax.lines:
        try:
            xdata = list(line.get_xdata())
            ydata = list(line.get_ydata())
        except TypeError:
            continue
        if len(xdata) == 2 and len(ydata) == 2:
            # Check for horizontal lines and discard
            if xdata == [0, 1] and ydata[0] == ydata[1]:
                continue
            # Check for vertical lines and discard
            if ydata == [0, 1] and xdata[0] == xdata[1]:
                continue
        else:
            max_values.append(max(ydata))
            min_values.append(min(ydata))
    if max_values and min_values:
        maximum = max(max_values)
        minimum = min(min_values)
        margin_height = (maximum - minimum) * margin
        ax.set_ylim(minimum - margin_height, maximum + margin_height)
