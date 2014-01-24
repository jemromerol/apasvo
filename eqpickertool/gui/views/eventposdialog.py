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


class EventPosDialog(QtGui.QDialog):
    """
    """

    valueChanged = QtCore.Signal(int)

    def __init__(self, record, event, parent=None):
        super(EventPosDialog, self).__init__(parent)
        self._record = record
        self._event = event
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("Event position")
        self.group_box = QtGui.QGroupBox(self)
        self.group_box.setTitle("Adjust event position")
        self.event_position_label = QtGui.QLabel("Event time (s):")
        self.event_position_time_edit = QtGui.QTimeEdit(self)
        self.event_position_time_edit.setDisplayFormat("hh:mm:ss.zzz")
        self.event_position_time_edit.setMinimumTime(QtCore.QTime().addMSecs(0))
        self.event_position_time_edit.setMaximumTime(QtCore.QTime().
                                                     addMSecs(int(1000 *
                                                                  len(self._record.signal) /
                                                                  self._record.fs)))
        self.event_position_time_edit.setTime(QtCore.QTime().
                                              addMSecs(int(1000 *
                                                           self._event.time /
                                                           self._record.fs)))
        self.cf_value_label = QtGui.QLabel("CF value:")
        self.cf_value_field = QtGui.QLabel("%.3g" % self._event.cf_value)
        self.cf_maximum_button = QtGui.QPushButton("Position event at CF maximum",
                                                   self)
        self.takanami_button = QtGui.QPushButton("Takanami adjust", self)
        self.form_layout = QtGui.QFormLayout(self.group_box)
        self.form_layout.setWidget(0, QtGui.QFormLayout.LabelRole,
                                   self.event_position_label)
        self.form_layout.setWidget(0, QtGui.QFormLayout.FieldRole,
                                   self.event_position_time_edit)
        self.form_layout.setWidget(1, QtGui.QFormLayout.LabelRole,
                                   self.cf_value_label)
        self.form_layout.setWidget(1, QtGui.QFormLayout.FieldRole,
                                   self.cf_value_field)
        self.form_layout.setWidget(2, QtGui.QFormLayout.SpanningRole,
                                   self.cf_maximum_button)
        self.form_layout.setWidget(3, QtGui.QFormLayout.SpanningRole,
                                   self.takanami_button)
        self.button_box = QtGui.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel |
                                           QtGui.QDialogButtonBox.Ok)
        self.vertical_layout = QtGui.QVBoxLayout(self)
        self.vertical_layout.addWidget(self.group_box)
        self.vertical_layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.event_position_time_edit.timeChanged.connect(self.on_position_changed)

    def on_position_changed(self, value):
        t = int((QtCore.QTime().msecsTo(value) / 1000.0) * self.data_fs)
        if t != self._event.time:
            self._event.time = t
            self.valueChanged.emit(self._event.time)














