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
import obspy as op
import eventcommands as commands
from apasvo.gui.views.settingsdialog import COLOR_KEYS
from apasvo.gui.views.settingsdialog import DEFAULT_COLOR_KEY
from apasvo.gui.views.settingsdialog import DEFAULT_COLOR_SCHEME
from apasvo.picking import apasvotrace as rc

from apasvo._version import _application_name
from apasvo._version import _organization


class EventListModel(QtCore.QAbstractTableModel):
    """A Table Model class to handle a list of seismic events.
    """

    emptyList = QtCore.Signal(bool)
    eventCreated = QtCore.Signal(rc.ApasvoEvent)
    eventDeleted = QtCore.Signal(rc.ApasvoEvent)
    eventModified = QtCore.Signal(rc.ApasvoEvent)
    detectionPerformed = QtCore.Signal()

    DEFAULT_ATTRIBUTES = [
        {'name': 'Label', 'type': 'event', 'attribute_name': 'name', 'editable': True},
        {'name': 'Time', 'type': 'event', 'attribute_name': 'time', 'editable': False,
         'attribute_type': 'date'},
        {'name': 'Sample', 'type': 'event', 'attribute_name': 'stime', 'editable': False},
        {'name': 'CF Value', 'type': 'event', 'attribute_name': 'cf_value', 'editable': False,
         'format': "{:.6g}"},
        {'name': 'Mode', 'type': 'event', 'attribute_name': 'evaluation_mode', 'editable': True,
         'attribute_type': 'enum', 'value_list': op.core.event_header.EvaluationMode.keys()},
        {'name': 'Phase hint', 'type': 'event', 'attribute_name': 'phase_hint', 'editable': True,
         'attribute_type': 'enum', 'value_list': rc.PHASE_VALUES},
        {'name': 'Method', 'type': 'event', 'attribute_name': 'method', 'editable': False,
         'attribute_type': 'enum', 'value_list': rc.ALLOWED_METHODS},
        {'name': 'Status', 'type': 'event', 'attribute_name': 'evaluation_status', 'editable': True,
         'attribute_type': 'enum', 'value_list': op.core.event_header.EvaluationStatus.keys()},
        {'name': 'Comments', 'type': 'event', 'attribute_name': 'comments', 'editable': True},
    ]

    def __init__(self, record, command_stack, attributes=None):
        QtCore.QAbstractTableModel.__init__(self)
        self.record = record
        self.attributes = attributes if attributes is not None else self.DEFAULT_ATTRIBUTES
        self.command_stack = command_stack
        self.color_key = None
        self.color_map = {}
        self.loadColorMap()

    @property
    def empty(self):
        return (len(self.record.events) != 0)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.record.events)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.attributes)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role == QtCore.Qt.DisplayRole:
            attribute = self.attributes[index.column()]
            data = None
            if attribute['type'] == 'event':
                data = self.record.events[index.row()].__getattribute__(attribute['attribute_name'])
            if attribute.get('attribute_type') == 'date':
                dateformat = attribute.get('dateformat')
                if dateformat is not None:
                    data = data.strftime(dateformat)
            rep_format = attribute.get('format', '{}')
            return rep_format.format(data)
        elif role == QtCore.Qt.BackgroundRole:
            return self.calculateEventColor(index)
        else:
            return None

    def calculateEventColor(self, index):
        if index.isValid():
            if self.color_key is not None:
                value = self.record.events[index.row()].__getattribute__(self.color_key)
                return self.color_map.get(value)
        return None

    def loadColorMap(self):
        settings = QtCore.QSettings(_organization, _application_name)
        self.color_map = {}
        # load color settings
        if "color_settings" in settings.childGroups():
            settings.beginGroup("color_settings")
            for key in settings.childKeys():
                if key == 'color_key':
                    self.color_key = COLOR_KEYS[int(settings.value(key))]
                else:
                    self.color_map[key] = QtGui.QColor(settings.value(key))
            settings.endGroup()
        # load default color scheme otherwise
        else:
            self.color_key = DEFAULT_COLOR_KEY
            for key, color in DEFAULT_COLOR_SCHEME:
                self.color_map[key] = QtGui.QColor(color)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.attributes[section].get('name')
        return None

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.command_stack.push(commands.SortEventList(self,
                                                       self.attributes[column]['attribute_name'],
                                                       order))

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            key = self.attributes[index.column()]['attribute_name']
            event = self.record.events[index.row()]
            if event.__getattribute__(key) != value:
                self.command_stack.push(commands.EditEvent(self, event,
                                                           **{key: value}))
            return True
        return False

    def editEvent(self, event, **kwargs):
        self.command_stack.push(commands.EditEvent(self, event, **kwargs))

    def flags(self, index):
        attribute = self.attributes[index.column()]
        if not attribute.get('editable'):
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        return (QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsEnabled)

    def removeRows(self, row_list, parent=QtCore.QModelIndex()):
        self.command_stack.push(commands.DeleteEvents(self, row_list))
        self.emptyList.emit(self.empty)

    def createEvent(self, time, name='', comments='', method=rc.method_other,
                    evaluation_mode=rc.mode_manual, evaluation_status=rc.status_preliminary):
        event = rc.ApasvoEvent(self.record, time, name=name, comments=comments,
                         method=method, evaluation_mode=evaluation_mode, evaluation_status=evaluation_status)
        self.addEvent(event)
        self.emptyList.emit(self.empty)
        return event

    def addEvent(self, event):
        self.command_stack.push(commands.AppendEvent(self, event))
        self.emptyList.emit(self.empty)

    def detectEvents(self, alg, **kwargs):
        self.command_stack.push(commands.DetectEvents(self, alg, **kwargs))
        self.emptyList.emit(self.empty)

    def clearEvents(self):
        if len(self.record.events) > 0:
            self.command_stack.push(commands.ClearEventList(self))
        self.emptyList.emit(self.empty)

    def updateList(self):
        self.modelAboutToBeReset.emit()
        self.emptyList.emit(self.empty)
        self.modelReset.emit()

    def indexOf(self, event):
        if event in self.record.events:
            return self.record.events.index(event)
        return None

    def getEventByRow(self, row):
        return self.record.events[row]
