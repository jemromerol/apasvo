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
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
from _version import _application_name
from _version import _organization


MINIMUM_MARGIN_IN_SECS = 0.5


class TakanamiTask(QtCore.QObject):
    """A class to handle a Takanami exec. task."""

    finished = QtCore.Signal()

    def __init__(self, event):
        super(TakamaniTask, self).__init__()
        self.event = event

    def run(self):
        self.event.record.refine_events(self.event)
        self.finished.emit()


class TakanamiDialog(QtGui.QDialog):

    def __init__(self, document, event, parent=None):
        super(TakanamiDialog, self).__init__(parent)
        self._init_ui()

        self.document = document
        self.event = event

        self._start = 0.0
        self._end = 0.0
        self.load_settings()

        self.simmetric_limits = True

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.clicked.connect(self.on_click)
        self.start_point_spinbox.timeChanged.connect(self.on_left_margin_changed)
        self.end_point_spinbox.timeChanged.connect(self.on_right_margin_changed)
        self.limits_checkbox.toogled.connect(self.toggle_simmetric_limits)
 
    def _init_ui(self):
        self.setWindowTitle("Takanami's Autoregressive Method")
        self.fig, _ = plt.subplots(2, 1, sharex=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumSize(self.canvas.size())
        self.position_label = QtGui.QLabel("Time: 00:00:00.000  CF value: 0.000")
        self.group_box = QtGui.QGroupBox(self)
        self.group_box.setTitle("Limits")
        self.limits_checkbox = QtGui.QCheckBox("Simmetric limits",
                                                self.group_box)
        self.limits_checkbox.setChecked(True)
        self.start_point_label = QtGui.QLabel("Start point:")
        self.start_point_spinbox = QtGui.QTimeEdit(self.group_box)
        self.start_point_spinbox.setMinimumTime(QtCore.QTime.addSecs(0))
        self.end_point_label = QtGui.QLabel("End point:")
        self.end_point_spinbox = QtGui.QTimeEdiTimeEdit(self.group_box)
        self.end_point_spinbox.setMinimumTime(QtCore.QTime.addSecs(0))
        self.group_box_layout = QtGui.QFormLayout(self.group_box)
        self.group_box_layout.setWidget(0, Qtgui.QFormLayout.SpanRole,
                                        self.limits_checkbox)
        self.group_box_layout.setWidget(1, QtGui.QFormLayout.LabelRole,
                                        self.start_point_label)
        self.group_box_layout.setWidget(1, QtGui.QFormLayout.FieldRole,
                                        self.start_point_spinbox)
        self.group_box_layout.setWidget(2, QtGui.QFormLayout.LabelRole,
                                        self.end_point_label)
        self.group_box_layout.setWidget(2, QtGui.QFormLayout.FieldRole,
                                        self.end_point_spinbox)
        self.button_box = QtGui.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.RestoreDefaults,
                                           QtGui.QDialogButtonBox.Cancel,
                                           QtGui.QDialogButtonBox.Ok)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.position_label)
        self.layout.addWidget(self.group_box)
        self.layout.addWidget(self.button_box)

       
    def on_click(self, button):
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.RestoreDefaults:
            self.load_settings()
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Ok:
            self.save_settings()

    def on_start_point_changed(self, value):
        t_start = int(max(0, (QtCore.QTime().msecsTo(value) / 1000.0) *
                          self.event.record.fs))
        if self._start != t_start:
            self_start = t_start
     

    def on_end_point_changed(self, value):
        t_end = int(min(len(event.record.signal,
                        (QtCore.QTime().msecsTo(value) / 1000.0) *
                         self.event.record.fs))
        if self._end != t_end:
            self._end = t_end
 
    def toggle_simmetric_limits(self, value):
        if self.simmetric_limits != value:
            self.simmetric_limits = value
            if self.simmetric_limits:
                minimum_margin = min(self.event.time - self._start,
                                     self.event.time - self._end)
                self.set_margin(minimum_margin)
     
    def load_settings(self):
         """Loads settings from persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("takanami_settings")
        default_margin = int(self.settings.value('takanami_margin', 5.0) * self.event.record.fs)
        settings.endGroup()
        self.set_margin(default_margin)
 
    def set_margin(self, margin):
        if margin <= 0:
            raise ValueError("margin must be a positive value")

        margin = max(MINIMUM_MARGIN_IN_SECS * self.event.record.fs, margin)
        self._start = max(0, self.event.time - margin)
        self._end = min(len(event.record.signal),
                        self.event.time + margin)
        self.start_point_spinbox.setTime(QtCore.QTime().
                                         addMSecs((self._start * 1000.0) /
                                                  self.event.record.fs))
        self.end_point_spinbox.setTime(QtCore.QTime().
                                       addMSecs((self._end * 1000.0) /
                                                self.event.record.fs))

    def apply_takanami(self):
        self._thread = QtCore.QThread(self)
        self._task = TakanamiTask(self.event)
        self._task.moveToThread(self._thread)
        self._thread.started.connect(self._task.run)
        self._task.finished.connect(self._thread.quit)
        self._task.finished.connect(self.accept)
        self._task.finished.connect(self._task.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()


     

















