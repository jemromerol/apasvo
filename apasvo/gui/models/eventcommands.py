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
from PySide import QtGui


class AppendEvent(QtGui.QUndoCommand):

    def __init__(self, model, event):
        super(AppendEvent, self).__init__('Create event')
        self.model = model
        self.event = event

    def undo(self):
        self.model.beginRemoveRows(QtCore.QModelIndex(), len(self.model.record.events) - 1,
                                   len(self.model.record.events) - 1)
        self.model.record.events.pop()
        self.model.eventDeleted.emit(self.event)
        self.model.endRemoveRows()

    def redo(self):
        self.model.beginInsertRows(QtCore.QModelIndex(), len(self.model.record.events),
                                   len(self.model.record.events))
        self.model.record.events.append(self.event)
        self.model.eventCreated.emit(self.event)
        self.model.endInsertRows()

    def id(self):
        return 1


class DeleteEvents(QtGui.QUndoCommand):

    def __init__(self, model, row_list):
        super(DeleteEvents, self).__init__('Delete events')
        self.model = model
        self.row_list = sorted(row_list)
        self.events = [self.model.record.events[i] for i in self.row_list]

    def undo(self):
        for row, event in zip(self.row_list, self.events):
            self.model.beginInsertRows(QtCore.QModelIndex(), row, row)
            self.model.record.events.insert(row, event)
            self.model.eventCreated.emit(event)
            self.model.endInsertRows()

    def redo(self):
        for row, event in zip(sorted(self.row_list, reverse=True), sorted(self.events, reverse=True)):
            self.model.beginRemoveRows(QtCore.QModelIndex(), row, row)
            self.model.record.events.remove(event)
            self.model.eventDeleted.emit(event)
            self.model.endRemoveRows()

    def id(self):
        return 2


class EditEvent(QtGui.QUndoCommand):

    def __init__(self, model, event, **kwargs):
        super(EditEvent, self).__init__('Edit event')
        self.model = model
        self.event = event
        self.params = kwargs
        self.old_params = {}
        for key in self.params.keys():
            self.old_params[key] = self.event.__getattribute__(key)

    def undo(self):
        self.model.layoutAboutToBeChanged.emit()
        for key, value in self.old_params.items():
            self.event.__setattr__(key, value)
        self.model.eventModified.emit(self.event)
        self.model.layoutChanged.emit()

    def redo(self):
        self.model.layoutAboutToBeChanged.emit()
        for key, value in self.params.items():
            self.event.__setattr__(key, value)
        self.model.eventModified.emit(self.event)
        self.model.layoutChanged.emit()

    def id(self):
        return 3


class ClearEventList(QtGui.QUndoCommand):

    def __init__(self, model):
        super(ClearEventList, self).__init__('Clear event list')
        self.model = model
        self.events = list(self.model.record.events)

    def undo(self):
        self.model.beginInsertRows(QtCore.QModelIndex(), 0,
                                   len(self.events) - 1)
        self.model.record.events = list(self.events)
        for event in self.model.record.events:
            self.model.eventCreated.emit(event)
        self.model.endInsertRows()

    def redo(self):
        self.model.beginRemoveRows(QtCore.QModelIndex(), 0,
                                   len(self.events) - 1)
        self.model.record.events = []
        for event in self.events:
            self.model.eventDeleted.emit(event)
        self.model.endRemoveRows()

    def id(self):
        return 4


class SortEventList(QtGui.QUndoCommand):

    def __init__(self, model, key, order):
        super(SortEventList, self).__init__('Sort event list')
        self.model = model
        self.key = key
        self.order = order
        self.old_events = list(self.model.record.events)

    def undo(self):
        self.model.layoutAboutToBeChanged.emit()
        self.model.record.events = list(self.old_events)
        self.model.layoutChanged.emit()

    def redo(self):
        self.model.layoutAboutToBeChanged.emit()
        self.model.record.sort_events(key=self.key,
                                reverse=(self.order == QtCore.Qt.DescendingOrder))
        self.model.layoutChanged.emit()

    def id(self):
        return 5


class DetectEvents(QtGui.QUndoCommand):

    def __init__(self, model, alg, **kwargs):
        super(DetectEvents, self).__init__('Apply %s' % alg.__class__.__name__.
                                           upper())
        self.model = model
        self.n_events_before = len(self.model.record.events)
        self.events = list(self.model.record.detect(alg, **kwargs))
        self.n_events_after = len(self.events)
        self.model.detectionPerformed.emit()

    def undo(self):
        self.model.beginRemoveRows(QtCore.QModelIndex(), self.n_events_before,
                                   self.n_events_after - 1)
        self.model.record.events = self.model.record.events[:self.n_events_before]
        for i in range(self.n_events_before, self.n_events_after):
            self.model.eventDeleted.emit(self.events[i])
        self.model.endRemoveRows()

    def redo(self):
        self.model.beginInsertRows(QtCore.QModelIndex(), self.n_events_before,
                                   self.n_events_after - 1)
        self.model.record.events = list(self.events)
        for i in range(self.n_events_before, self.n_events_after):
            self.model.eventCreated.emit(self.events[i])
        self.model.endInsertRows()

    def id(self):
        return 6












