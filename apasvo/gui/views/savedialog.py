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

from PySide import QtGui
from apasvo.gui.views.generated import ui_savedialog
from apasvo.utils import futils
from apasvo.utils.formats import rawfile


FORMATS = (rawfile.format_binary, rawfile.format_text)
FORMATS_LABELS = ('Binary', 'Text')
DTYPES = (rawfile.datatype_int16,
          rawfile.datatype_int32,
          rawfile.datatype_int64,
          rawfile.datatype_float16,
          rawfile.datatype_float32,
          rawfile.datatype_float64, )
DTYPES_LABELS = ('16 bits, PCM',
                 '32 bits, PCM',
                 '64 bits, PCM',
                 '16 bits, float',
                 '32 bits, float',
                 '64 bits, float', )
BYTEORDERS = (rawfile.byteorder_little_endian,
              rawfile.byteorder_big_endian)
BYTEORDERS_LABELS = ('Little Endian (Intel)', 'Big Endian (Motorola)')


class SaveDialog(QtGui.QDialog, ui_savedialog.Ui_SaveDialog):
    """A dialog window to save seismic data to a binary or text file.

    Allows the user to choose several settings in order to save a seismic
    signal, i.e.:
        Format: Binary or text format.
        Data-type: PCM 16, PCM 32, PCM 64, Float16, Float32 or Float64,
        Endianness: Little-endian or big-endian.

    Attributes:
        fmt: Default file format. Available values are 'binary' and 'text'.
            Default: 'binary'.
        dtype: Default datatype. Available values are 'int16', 'int32', 'int64',
            'float16', 'float32' and 'float64'.
            Default: 'float64'.
        byteorder: Default endianness. Available values are 'little-endian',
            'big-endian' and 'native'.
            Default: 'native'.
    """

    def __init__(self, parent, fmt='binary', dtype='float64', byteorder='native'):
        super(SaveDialog, self).__init__(parent)
        self.setupUi(self)
        # init comboboxes
        self.FileFormatComboBox.addItems(FORMATS_LABELS)
        self.DataTypeComboBox.addItems(DTYPES_LABELS)
        self.ByteOrderComboBox.addItems(BYTEORDERS_LABELS)

        self.FileFormatComboBox.currentIndexChanged.connect(self.on_format_change)
        # Set defaults
        self.FileFormatComboBox.setCurrentIndex(FORMATS.index(fmt))
        self.DataTypeComboBox.setCurrentIndex(DTYPES.index(dtype))
        # Detect endianness if 'native' byteorder is selected
        if byteorder == rawfile.byteorder_native:
            if futils.is_little_endian():
                self.ByteOrderComboBox.setCurrentIndex(BYTEORDERS.index(rawfile.byteorder_little_endian))
            else:
                self.ByteOrderComboBox.setCurrentIndex(BYTEORDERS.index(rawfile.byteorder_big_endian))
        else:
            self.ByteOrderComboBox.setCurrentIndex(BYTEORDERS.index(byteorder))

    def on_format_change(self, idx):
        """Updates UI after toggling the format value."""
        fmt = FORMATS[self.FileFormatComboBox.currentIndex()]
        if fmt == rawfile.format_binary:
            self.DataTypeComboBox.setVisible(True)
            self.DataTypeLabel.setVisible(True)
            self.ByteOrderComboBox.setVisible(True)
            self.ByteOrderLabel.setVisible(True)
        elif fmt == rawfile.format_text:
            self.DataTypeComboBox.setVisible(False)
            self.DataTypeLabel.setVisible(False)
            self.ByteOrderComboBox.setVisible(False)
            self.ByteOrderLabel.setVisible(False)

    def get_values(self):
        """Gets selected parameters."""
        return {'fmt': FORMATS[self.FileFormatComboBox.currentIndex()],
                'dtype': DTYPES[self.DataTypeComboBox.currentIndex()],
                'byteorder': BYTEORDERS[self.ByteOrderComboBox.currentIndex()]}
