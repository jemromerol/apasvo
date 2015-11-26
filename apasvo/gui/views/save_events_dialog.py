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
from apasvo.gui.views.generated import ui_save_events_dialog


FORMATS = ('JSON', 'NLLOC_OBS', 'QUAKEML')
DEFAULT_FORMAT = 'NLLOC_OBS'
FORMATS_LABELS = ('JSON', 'NonLinLoc', 'QuakeML')


class SaveEventsDialog(QtGui.QDialog, ui_save_events_dialog.Ui_SaveEventsDialog):
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

    def __init__(self, parent, fmt=None):
        fmt = fmt if fmt is not None else DEFAULT_FORMAT
        super(SaveEventsDialog, self).__init__(parent)
        self.setupUi(self)
        # init comboboxes
        self.FileFormatComboBox.addItems(FORMATS_LABELS)
        # Set defaults
        self.FileFormatComboBox.setCurrentIndex(FORMATS.index(fmt))

    def get_values(self):
        """Gets selected parameters."""
        return {'fmt': FORMATS[self.FileFormatComboBox.currentIndex()]}
