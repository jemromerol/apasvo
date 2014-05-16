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

from PySide import QtCore


class FilterListModel(QtCore.QAbstractTableModel):
    """A Table Model class to handle a list of length values.
    """

    sizeChanged = QtCore.Signal(int)

    def __init__(self, listobj, header=None):
        QtCore.QAbstractTableModel.__init__(self)
        self._list = listobj
        if header is None:
            header = ['Length (in seconds)']
        self._header = header

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return "%s" % self._list[index.row()]

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._header[section]
        return None

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._list.sort(reverse=(order == QtCore.Qt.DescendingOrder))
        self.layoutChanged.emit()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            self._list[index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return (QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsEnabled)

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        if row < 0 or row > len(self._list):
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        while count != 0:
            del self._list[row]
            count -= 1
        self.sizeChanged.emit(len(self._list))
        self.endRemoveRows()
        return True

    def addFilter(self, value=10.0):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._list),
                             len(self._list))
        self._list.append(value)
        self.sizeChanged.emit(len(self._list))
        self.endInsertRows()

    def clearFilters(self):
        if self.rowCount() > 0:
            self.removeRows(0, self.rowCount())

    def list(self):
        return self._list

