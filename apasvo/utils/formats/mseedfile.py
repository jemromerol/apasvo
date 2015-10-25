# encoding: utf-8
'''
@author:     Jose Emilio Romero Lopez

@copyright:  Copyright 2013-2015, Jose Emilio Romero Lopez.

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
import struct
import datetime


class mSEEDFile(object):
    """A mSEED file.

    Attributes:
        filename: Name of the file
    """
    def __init__(self):
        """Inits a mSEEDFile object.

        Args:
            filename: Name of the file.
        """
        super(mSEEDFile, self).__init__()
        self.byte_order = '>'
        self.header = {}
        self.data = np.array([], dtype='float64')
        self.time = np.array([], dtype='datetime64')

    def read(self, fp, **kwargs):
        try:
            file_in = open(fp, 'rb')
        except:
            #Assume fp is a file-like object
            file_in = fp

    def write(self, fp, **kwargs):
        try:
            file_out = open(fp, 'wb')
        except:
            #Assume fp is a file-like object
            file_out = fp









