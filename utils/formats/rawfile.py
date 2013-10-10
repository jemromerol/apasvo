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

from utils import futils


class RawFile(object):

    def __init__(self):
        self.datatypes = {'float16': 'f2', 'float32': 'f4', 'float64': 'f8'}
        self.byteorders = {'little-endian': '<', 'big-endian': '>', 'native': '='}

    def read(self):
        raise NotImplementedError

    def read_in_blocks(self, block_size):
        raise NotImplementedError

    def write(self, array):
        raise NotImplementedError


class BinFile(RawFile):

    def __init__(self, filename, dtype='float64', byteorder='native'):
        super(BinFile, self).__init__()
        self.dtype = np.dtype(self.byteorders[byteorder] + self.datatypes[dtype])
        self.filename = filename

    def read(self):
        return np.fromfile(self.filename, dtype=self.dtype)

    def read_in_blocks(self, block_size=1024):
        with open(self.filename, 'rb') as f:
            chunk_size = block_size * self.dtype.itemsize
            for data in futils.read_in_chunks(f, chunk_size):
                yield np.frombuffer(data, dtype=self.dtype)

    def write(self, array):
        return array.tofile(self.filename)


class TextFile(RawFile):

    def __init__(self, filename, dtype='float64', byteorder='native'):
        super(TextFile, self).__init__()
        self.dtype = np.dtype(self.byteorders[byteorder] + self.datatypes[dtype])
        self.filename = filename

    def read(self, **kwargs):
        return np.loadtxt(self.filename, dtype=self.dtype, **kwargs)

    def read_in_blocks(self, block_size=1024):
        with open(self.filename, 'r') as f:
            for data in futils.read_txt_in_chunks(f, block_size):
                yield np.array(data, dtype=self.dtype)

    def write(self, array, **kwargs):
        return np.savetxt(self.filename, array, **kwargs)


def get_file_handler(filename, fmt='', dtype='float64', byteorder='native', **kwargs):
    if isinstance(filename, file):
        filename = filename.name
    formats = ['binary', 'text']
    if fmt not in formats:
        fmt = 'text' if futils.istextfile(filename) else 'binary'
    if fmt == 'text':
        return TextFile(filename, dtype=dtype, byteorder=byteorder)
    else:
        return BinFile(filename, dtype=dtype, byteorder=byteorder)
