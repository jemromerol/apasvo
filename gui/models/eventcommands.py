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
from PySide import QtGui


class AppendEvent(QtGui.QUndoCommand):

    def __init__(self, model, event):
        super(AppendEvent, self).__init__('Create event')
        self.model = model
        self.event = event

    def undo(self):
        self.model.record.events.pop()
        self.model.eventDeleted.emit(self.event)

    def redo(self):
        self.model.record.events.append(self.event)
        self.model.eventCreated.emit(self.event)

    def id(self):
        return 1


class DeleteEvent(QtGui.QUndoCommand):

    def __init__(self, model, event):
        super(DeleteEvent, self).__init__('Delete event')
        self.model = model
        self.event = event
        self.position = self.model.record.events.index(self.event)

    def undo(self):
        self.model.record.events.insert(self.position, self.event)
        self.model.eventCreated.emit(self.event)

    def redo(self):
        self.model.record.events.pop(self.position)
        self.model.eventDeleted.emit(self.event)

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
        for key, value in self.old_params.items():
            self.event.__setattr__(key, value)
        self.model.eventModified.emit(self.event)

    def redo(self):
        for key, value in self.params.items():
            self.event.__setattr__(key, value)
        self.model.eventModified.emit(self.event)

    def id(self):
        return 3


class ClearEventList(QtGui.QUndoCommand):

    def __init__(self, model):
        super(ClearEventList, self).__init__('Clear event list')
        self.model = model
        self.events = self.model.record.events

    def undo(self):
        self.model.record.events = self.events
        for event in self.model.record.events:
            self.model.eventCreated.emit(event)

    def redo(self):
        self.model.record.events = []
        for event in self.model.record.events:
            self.model.eventDeleted.emit(event)

    def id(self):
        return 4


class SortEventList(QtGui.QUndoCommand):

    def __init__(self, model, key, order):
        super(SortEventList, self).__init__('Sort event list')
        self.model = model
        self.key = key
        self.order = order
        self.old_events = self.model.record.events

    def undo(self):
        self.model.record.events = self.old_events

    def redo(self):
        self.model.record.sort_events(key=self.key,
                                reverse=(self.order == QtCore.Qt.DescendingOrder))

    def id(self):
        return 5


class DetectEvents(QtGui.QUndoCommand):

    def __init__(self, model, alg, **kwargs):
        super(DetectEvents, self).__init__('Apply %s' % alg.__class__.__name__.
                                           upper())
        self.model = model
        self.alg = alg
        self.old_events = self.model.record.events
        self.params = kwargs

    def undo(self):
        for event in self.model.record.events:
            self.model.eventDeleted.emit(event)
        self.model.record.events = self.old_events
        for event in self.old_events:
            self.model.eventCreated.emit(event)

    def redo(self):
        for event in self.old_events:
            self.model.eventDeleted.emit(event)
        self.model.record.detect(self.alg, **self.params)
        self.model.detectionPerformed.emit()
        for event in self.model.record.events:
            self.model.eventCreated.emit(event)

    def id(self):
        return 6












