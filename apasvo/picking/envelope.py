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

from scipy import fftpack


def envelope(x):
    """Computes the envelope of a seismic signal.

    The envelope, e(n), of a signal x(n), is calculated as:

        e(n) = (x(n) ** 2 + h(n) ** 2) ** 0.5

    where h(n) is the Hilbert Transform of x(n)

    Args:
        x: array of data.

    Returns:
        out: Envelope of x, numpy array type.
    """
    return (x ** 2 + fftpack.hilbert(x) ** 2) ** 0.5
