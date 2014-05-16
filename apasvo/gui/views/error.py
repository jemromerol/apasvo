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


def display_error_dlg(msg, additional_info=None, parent=None):
    """Displays an error dialog."""
    msgBox = QtGui.QMessageBox(parent)
    msgBox.setText("An error occurred:")
    horizontalSpacer = QtGui.QSpacerItem(320, 0, QtGui.QSizePolicy.Minimum,
                                         QtGui.QSizePolicy.Expanding)
    layout = msgBox.layout()
    layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())
    msgBox.setIcon(QtGui.QMessageBox.Critical)
    msgBox.setInformativeText(msg)
    if additional_info is not None:
        msgBox.setDetailedText(additional_info)
    msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
    msgBox.exec_()
