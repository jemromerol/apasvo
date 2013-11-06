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

from PySide import QtCore
import datetime


class EventListModel(QtCore.QAbstractTableModel):
    """
    """

    emptyList = QtCore.Signal(bool)

    def __init__(self, record, header):
        QtCore.QAbstractTableModel.__init__(self)
        self._record = record
        self._list = self._record.events
        self._header = header
        self.empty = (len(self._list) != 0)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        attr_name = self._header[index.column()]
        data = self._list[index.row()].__getattribute__(attr_name)
        if attr_name == 'time':
            return str(datetime.timedelta(seconds=data))
        if attr_name == 'cf_value':
            return "%.3f" % data
        return "%s" % data

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._header[section].replace('_', ' ').title()
        return None

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._record.sort_events(key=self._header[column],
                                 reverse=(order == QtCore.Qt.DescendingOrder))
        self._list = self._record.events
        self.layoutChanged.emit()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            self._list[index.row()].__setattr__(self._header[index.column()], value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        attr_name = self._header[index.column()]
        if attr_name in ['time', 'cf_value', 'mode', 'method']:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        return (QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsEnabled)

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        if row < 0 or row > len(self._list):
            return
        self.beginRemoveRows(parent, row, row + count - 1)
        while count != 0:
            del self._list[row]
            count -= 1
        self._setEmpty()
        self.endRemoveRows()

    def addEvent(self, event):
        """"""
        self.beginInsertRows(QtCore.QModelIndex(), len(self._list),
                             len(self._list))
        self._list.append(event)
        self._setEmpty()
        self.endInsertRows()

    def _setEmpty(self):
        """"""
        empty = (len(self._list) != 0)
        if self.empty != empty:
            self.empty = empty
            self.emptyList.emit(empty)

    def updateList(self):
        """"""
        self.modelAboutToBeReset.emit()
        self._list = self._record.events
        self._setEmpty()
        self.modelReset.emit()

