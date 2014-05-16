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

from PySide import QtGui, QtCore


class DoubleSpinBoxDelegate(QtGui.QStyledItemDelegate):
    """A delegate class displaying a double spin box."""

    def __init__(self, parent=None, minimum=0.0, maximum=100.0, step=0.01):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self._min = minimum
        self._max = maximum
        self._step = step

    def createEditor(self, parent, option, index):
        editor = QtGui.QDoubleSpinBox(parent)
        editor.setMinimum(self._min)
        editor.setMaximum(self._max)
        editor.setSingleStep(self._step)
        editor.setAccelerated(True)
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, spinBox, index):
        value = float(index.model().data(index, QtCore.Qt.DisplayRole))
        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        value = spinBox.value()
        model.setData(index, value)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
