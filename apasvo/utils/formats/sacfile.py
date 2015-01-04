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


#HEADER FIELDS
HEADER_FLOAT_FIELDS = (
'DELTA',   'DEPMIN',  'DEPMAX',  'SCALE',  'ODELTA',
'B',       'E',       'O',       'A',      'INTERNAL',
'T0',      'T1',      'T2',      'T3',     'T4',
'T5',      'T6',      'T7',      'T8',     'T9',
'F',       'RESP0',   'RESP1',   'RESP2',  'RESP3',
'RESP4',   'RESP5',   'RESP6',   'RESP7',  'RESP8',
'RESP9',   'STLA',    'STLO',    'STEL',   'STDP',
'EVLA',    'EVLO',    'EVEL',    'EVDP',   'MAG',
'USER0',   'USER1',   'USER2',   'USER3',  'USER4',
'USER5',   'USER6',   'USER7',   'USER8',  'USER9',
'DIST',    'AZ',      'BAZ',     'GCARC',  'INTERNAL',
'INTERNAL', 'DEPMEN',  'CMPAZ',   'CMPINC', 'XMINIMUM',
'XMAXIMUM', 'YMINIMUM', 'YMAXIMUM', 'UNUSED', 'UNUSED',
'UNUSED',  'UNUSED',  'UNUSED',  'UNUSED', 'UNUSED',
)

HEADER_INTEGER_FIELDS = (
'NZYEAR',  'NZJDAY',  'NZHOUR',  'NZMIN',  'NZSEC',
'NZMSEC',  'NVHDR',   'NORID',   'NEVID',  'NPTS',
'INTERNAL', 'NWFID',   'NXSIZE',  'NYSIZE', 'UNUSED',
'IFTYPE',  'IDEP',    'IZTYPE',  'UNUSED', 'IINST',
'ISTREG',  'IEVREG',  'IEVTYP',  'IQUAL',  'ISYNTH',
'IMAGTYP', 'IMAGSRC', 'UNUSED',  'UNUSED', 'UNUSED',
'UNUSED',  'UNUSED',  'UNUSED',  'UNUSED', 'UNUSED',
)

HEADER_LOGICAL_FIELDS = (
'LEVEN',   'LPSPOL',  'LOVROK',  'LCALDA', 'UNUSED',
)

HEADER_ALPHANUMERIC_FIELDS = (
'KSTNM',  'KEVNM0', 'KEVNM1',
'KHOLE',  'KO',     'KA',
'KT0',    'KT1',    'KT2',
'KT3',    'KT4',    'KT5',
'KT6',    'KT7',    'KT8',
'KT9',    'KF',     'KUSER0',
'KUSER1', 'KUSER2', 'KCMPNM',
'KNETWK', 'KDATRD', 'KINST',
)


class SACFile(object):
    """A SAC file.

    Attributes:
        filename: Name of the file
    """
    def __init__(self):
        """Inits a SACFile object.

        Args:
            filename: Name of the file.
        """
        super(SACFile, self).__init__()
        self.byte_order = '>'
        self.header = {'NPTS': -12345,
                       'NVHDR': 6,
                       'B': -12345.0,
                       'E': -12345.0,
                       'IFTYPE': 1,
                       'LEVEN': True,
                       'DELTA': -12345.0}
        self.data = np.array([], dtype='float64')
        self.time = np.array([], dtype='datetime64')

    def read(self, fp, **kwargs):
        try:
            file_in = open(fp, 'rb')
        except:
            #Assume fp is a file-like object
            file_in = fp

        header = file_in.read(158 * 4)  #Header length is 158 words
        #Check header version & byte order
        NVHDR = struct.unpack(">i", header[76 * 4:77 * 4])[0]
        self.byte_order = "<" if NVHDR > 6 else ">"

        #Read float fields
        data = struct.unpack("%s70f" % self.byte_order, header[:70 * 4])
        for field_name, field in zip(HEADER_FLOAT_FIELDS, data):
            if field_name != 'UNUSED':
                self.header[field_name] = field
        #Read integer fields
        data = struct.unpack("%s35i" % self.byte_order, header[70 * 4:105 * 4])
        for field_name, field in zip(HEADER_INTEGER_FIELDS, data):
            if field_name != 'UNUSED':
                self.header[field_name] = field
        #Read logical fields
        data = struct.unpack("%s5i" % self.byte_order, header[105 * 4:110 * 4])
        for field_name, field in zip(HEADER_LOGICAL_FIELDS, data):
            if field_name != 'UNUSED':
                self.header[field_name] = bool(field)
        #Read alphanumeric fields
        data = [str(header[n * 4:(n + 2) * 4]) for n in range(110, 158, 2)]
        for field_name, field in zip(HEADER_ALPHANUMERIC_FIELDS, data):
            if field_name != 'UNUSED':
                self.header[field_name] = field.replace('\x00', '')
        #Concatenate KEVNM (see IRIS format)
        self.header['KEVNM'] = "%s%s" % (self.header['KEVNM0'], self.header['KEVNM1'])
        del self.header['KEVNM0']
        del self.header['KEVNM1']

        #Read Data Section
        data = file_in.read(self.header['NPTS'] * 4)
        self.data = np.array(struct.unpack("%s%sf" % (self.byte_order, self.header['NPTS']), data),
                             dtype='float64')

        #Create time vector
        start_time = datetime.datetime.strptime("%s%s%s%s%s%s" % (self.header['NZYEAR'],
                                                                  self.header['NZJDAY'],
                                                                  self.header['NZHOUR'],
                                                                  self.header['NZMIN'],
                                                                  self.header['NZSEC'],
                                                                  self.header['NZMSEC'] * 1000),
                                                "%Y%j%H%M%S%f")
        end_time = start_time + datetime.timedelta(seconds = (self.header['DELTA'] * self.header['NPTS']))
        step = datetime.timedelta(seconds = self.header['DELTA'])
        self.time = np.arange(start_time, end_time, step)

    def write(self, fp, **kwargs):
        try:
            file_out = open(fp, 'wb')
        except:
            #Assume fp is a file-like object
            file_out = fp

        #Store header
        header = []
        # Store float fields
        unused = struct.pack("%sf" % self.byte_order, -12345.0)
        for field in HEADER_FLOAT_FIELDS:
            if field == 'UNUSED':
                header.append(unused)
            else:
                header.append(struct.pack("%sf" % self.byte_order, self.header[field]))
        # Store integer fields
        unused = struct.pack("%si" % self.byte_order, -12345)
        for field in HEADER_INTEGER_FIELDS:
            if field == 'UNUSED':
                header.append(unused)
            else:
                header.append(struct.pack("%si" % self.byte_order, self.header[field]))
        # Store logical fields
        unused = struct.pack("%si" % self.byte_order, False)
        for field in HEADER_LOGICAL_FIELDS:
            if field == 'UNUSED':
                header.append(unused)
            else:
                header.append(struct.pack("%si" % self.byte_order, self.header[field]))
        # Store alphanumeric fields
        for field in HEADER_ALPHANUMERIC_FIELDS:
            if field == 'KEVNM0':
                header.append(struct.pack("%s16s" % self.byte_order, self.header['KEVNM']))
            elif field == 'KEVNM1':
                pass
            else:
                header.append(struct.pack("%s8s" % self.byte_order, self.header[field]))

        #Store data section
        data = self.data.astype('%sf' % self.byte_order).tostring()

        file_out.write("%s%s" % (''.join(header), data))
        file_out.flush()




