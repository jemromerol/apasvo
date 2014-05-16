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


def find_peaks(x, threshold=None, order=1):
    """Finds local maxima of a function.

    Args:
        x: A data vector.
        threshold: Local maxima under this value will be discarded.
            If threshold is None, the function will return only the global
            maximum.
            Defaut value os None.
        order: Number of samples before and after a data point that have
            to be smaller than the data point to be considered a local maximum.
            If 'threshold' is None, this argument has no effect.
            Default: 1.
    Returns:
        out: A list of local maxima, numpy array type.
    """
    if threshold is not None:
        event_peaks = signal.argrelmax(x, order=int(order))[0]
        if event_peaks.size > 0:
            return event_peaks[x[event_peaks] > threshold]
        return event_peaks
    else:
        if x.size > 0:
            return np.array([np.argmax(x)])
        return np.array([])
