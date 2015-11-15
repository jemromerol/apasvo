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

import matplotlib
matplotlib.rcParams['backend'] = 'qt4agg'
matplotlib.rcParams['backend.qt4'] = 'PySide'
matplotlib.rcParams['patch.antialiased'] = False
matplotlib.rcParams['agg.path.chunksize'] = 80000
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from apasvo.gui.views import navigationtoolbar
from apasvo.gui.views import processingdialog
from apasvo.utils import clt
import matplotlib.pyplot as plt

import numpy as np
import traceback
from apasvo.picking import apasvotrace as rc
from apasvo.picking import takanami
from apasvo._version import _application_name
from apasvo._version import _organization

MINIMUM_MARGIN_IN_SECS = 0.5


class StreamPickingTask(QtCore.QObject):
    """A class to handle a Takanami exec. task.

    Attributes:
        record: An opened seismic record.
        start: Start point of the signal segment where
            the algorithm is going to be applied.
        end: End point of the signal segment where
            the algorithm is going to be applied.

    Signals:
        finished: Task finishes.
        position_estimated: Return values of Takanami method are ready.
    """

    finished = QtCore.Signal()
    error = QtCore.Signal(str, str)
    position_estimated = QtCore.Signal(int, np.ndarray, int)

    def __init__(self, record, start, end):
        super(StreamPickingTask, self).__init__()
        self.record = record
        self.start = start
        self.end = end
        self.algorithm = takanami.Takanami()
        self._abort = False

    def run(self):
        self._abort = False
        start_time_in_secs = max(0.0, self.start) / self.record.fs
        end_time_in_secs = (min(len(self.record.signal), self.end) /
                            self.record.fs)
        if self._abort:  # checkpoint
            return
        try:
            et, aic, n0_aic = self.algorithm.run(self.record.signal,
                                                 self.record.fs,
                                                 start_time_in_secs,
                                                 end_time_in_secs)
        except Exception, e:
            self.error.emit(str(e), traceback.format_exc())
            return
        if self._abort:  # checkpoint
            return
        self.position_estimated.emit(et, aic, n0_aic)
        self.finished.emit()

    def abort(self):
        self._abort = True


class TraceSelectorDialog(QtGui.QDialog):
    """A dialog to apply Takanami's AR picking method to a selected piece of a
    seismic signal.

    Attributes:
        document: Current opened document containing a seismic record.
        seismic_event: A seismic event to be refined by using Takanami method.
            If no event is provided, then a new seismic event will be created
            by using the estimated arrival time after clicking on 'Accept'
    """

    closed = QtCore.Signal()
    selection_changed = QtCore.Signal(int)

    def __init__(self, stream, parent=None):
        super(TraceSelectorDialog, self).__init__(parent)

        self.stream = stream

        self._init_ui()


    def _init_ui(self):
        self.setWindowTitle("Takanami's Autoregressive Method")
        self.fig, _ = plt.subplots(2, 1, sharex=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumSize(self.canvas.size())
        self.canvas.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding,
                                                    QtGui.QSizePolicy.Policy.Expanding))
        self.toolBarNavigation = navigationtoolbar.NavigationToolBar(self.canvas, self)
        self.position_label = QtGui.QLabel("Estimated Arrival Time: 00 h 00 m 00.000 s")
        self.group_box = QtGui.QGroupBox(self)
        self.group_box.setTitle("Limits")
        self.start_point_label = QtGui.QLabel("Start point:")
        self.start_point_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))
        self.start_point_spinbox = QtGui.QTimeEdit(self.group_box)
        self.start_point_spinbox.setDisplayFormat("hh 'h' mm 'm' ss.zzz 's'")
        self.end_point_label = QtGui.QLabel("End point:")
        self.end_point_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))
        self.end_point_spinbox = QtGui.QTimeEdit(self.group_box)
        self.end_point_spinbox.setDisplayFormat("hh 'h' mm 'm' ss.zzz 's'")
        self.group_box_layout = QtGui.QHBoxLayout(self.group_box)
        self.group_box_layout.setContentsMargins(9, 9, 9, 9)
        self.group_box_layout.setSpacing(12)
        self.group_box_layout.addWidget(self.start_point_label)
        self.group_box_layout.addWidget(self.start_point_spinbox)
        self.group_box_layout.addWidget(self.end_point_label)
        self.group_box_layout.addWidget(self.end_point_spinbox)
        self.button_box = QtGui.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Apply |
                                           QtGui.QDialogButtonBox.Cancel |
                                           QtGui.QDialogButtonBox.Ok)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(9, 9, 9, 9)
        self.layout.setSpacing(6)
        self.layout.addWidget(self.toolBarNavigation)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.position_label)
        self.layout.addWidget(self.group_box)
        self.layout.addWidget(self.button_box)

    def closeEvent(self, event):
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("geometry")
        settings.setValue("trace_selector", self.saveGeometry())
        settings.endGroup()
        self.closed.emit()
        super(TraceSelectorDialog, self).closeEvent(event)

    def showEvent(self, event):
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("geometry")
        self.restoreGeometry(settings.value("trace_selector"))
        settings.endGroup()
        super(TraceSelectorDialog, self).showEvent(event)

    def refresh(self):
        pass

    def load_settings(self):
        """Loads settings from persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("takanami_settings")
        self.default_margin = int(float(settings.value('takanami_margin', 5.0)) *
                             self.record.fs)
        settings.endGroup()

