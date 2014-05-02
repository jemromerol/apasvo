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
from apasvo.gui.views.generated import ui_loaddialog
from apasvo.utils import futils
from apasvo.utils.formats import rawfile


class LoadDialog(QtGui.QDialog, ui_loaddialog.Ui_LoadDialog):
    """A dialog window to load seismic data stored in a binary or text file.

    Allows the user to choose several settings in order to load a seismic
    signal, i.e.:
        Format: Binary or text format.
        Data-type: Float16, Float32 or Float64,
        Endianness: Little-endian or big-endian.
        Sample rate.

    The class also infers the right parameters for the chosen file and shows
    a preview of the loaded data for the selected parameters.

    Attributes:
        filename: Name of the opened file.
    """
    _formats = (rawfile.format_binary, rawfile.format_text)
    _dtypes = (rawfile.datatype_float16, rawfile.datatype_float32,
               rawfile.datatype_float64)
    _byteorders = (rawfile.byteorder_little_endian,
                   rawfile.byteorder_big_endian)

    def __init__(self, parent, filename):
        super(LoadDialog, self).__init__(parent)
        self.setupUi(self)
        self.filename = filename

        self.FileFormatComboBox.currentIndexChanged.connect(self.on_format_change)
        self.FileFormatComboBox.currentIndexChanged.connect(self.load_preview)
        self.DataTypeComboBox.currentIndexChanged.connect(self.load_preview)
        self.ByteOrderComboBox.currentIndexChanged.connect(self.load_preview)

        # Detect settings
        if futils.istextfile(self.filename):
            self.FileFormatComboBox.setCurrentIndex(1)
            # Detect sample rate
            fs = futils.get_sample_rate(filename)
            if fs:
                self.SampleFrequencySpinBox.setValue(fs)
        else:
            self.FileFormatComboBox.setCurrentIndex(0)
        if futils.is_little_endian():
            self.ByteOrderComboBox.setCurrentIndex(0)
        else:
            self.ByteOrderComboBox.setCurrentIndex(1)
        self.load_preview()

    def on_format_change(self, idx):
        """Updates UI after toggling the format value."""
        fmt = self._formats[self.FileFormatComboBox.currentIndex()]
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

    def load_preview(self):
        """Shows a preview of loaded data using the selected parameters."""
        # Load parameters
        values = self.get_values()
        # Set up a file handler according to the type of raw data (binary or text)
        fhandler = rawfile.get_file_handler(self.filename, **values)
        # Print data preview
        array = fhandler.read_in_blocks().next()
        data = ''
        for x in array:
            data += ("%s\n" % x)
        self.PreviewTextEdit.clear()
        self.PreviewTextEdit.setText(data)

    def get_values(self):
        """Gets selected parameters."""
        return {'fmt': self._formats[self.FileFormatComboBox.currentIndex()],
                'dtype': self._dtypes[self.DataTypeComboBox.currentIndex()],
                'byteorder': self._byteorders[self.ByteOrderComboBox.currentIndex()],
                'fs': float(self.SampleFrequencySpinBox.value())}
