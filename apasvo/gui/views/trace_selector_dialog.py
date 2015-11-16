# encoding: utf-8
'''
@author:     Jose Emilio Romero Lopez

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

from apasvo.gui.views import navigationtoolbar
from apasvo.gui.views import processingdialog
from apasvo.gui.views import tsvwidget

import numpy as np
import traceback
from apasvo.picking import takanami
from apasvo._version import _application_name
from apasvo._version import _organization


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


class TraceSelectorDialog(QtGui.QMainWindow):
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

    def __init__(self, stream, parent):
        super(TraceSelectorDialog, self).__init__(parent)

        self.main_window = parent
        self.stream = stream
        self._init_ui()

        # Connect signals


    def _init_ui(self):
        self.setWindowTitle("Opened Traces")
        # Create main structure
        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setVisible(False)
        self.setCentralWidget(self.centralwidget)
        self.layout = QtGui.QVBoxLayout(self.centralwidget)
        self.stream_viewer = tsvwidget.StreamViewerWidget(self)
        self.layout.addWidget(self.stream_viewer)

        # Add main toolbar
        self.tool_bar_main = QtGui.QToolBar(self)
        self.action_save = QtGui.QAction(self)
        self.action_save.setIcon(QtGui.QIcon(":/save.png"))
        self.action_save.setEnabled(False)
        self.action_close = QtGui.QAction(self)
        self.action_close.setIcon(QtGui.QIcon(":/close.png"))
        self.action_close.setEnabled(False)
        self.tool_bar_main.addAction(self.action_save)
        self.tool_bar_main.addAction(self.action_close)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.tool_bar_main)

        # Add analysis toolbar
        self.tool_bar_analysis = QtGui.QToolBar(self)
        self.action_sta_lta = QtGui.QAction(self)
        self.action_sta_lta.setIcon(QtGui.QIcon(":/stalta.png"))
        self.action_sta_lta.setEnabled(False)
        self.action_sta_lta.setToolTip("Apply STA-LTA algorithm")
        self.action_ampa = QtGui.QAction(self)
        self.action_ampa.setIcon(QtGui.QIcon(":/ampa.png"))
        self.action_ampa.setEnabled(False)
        self.action_ampa.setToolTip("Apply AMPA algorithm")
        self.tool_bar_analysis.addAction(self.action_sta_lta)
        self.tool_bar_analysis.addAction(self.action_ampa)
        # self.tool_bar_analysis.addSeparator()
        # self.action_activate_threshold = QtGui.QAction(self)
        # self.action_activate_threshold.setIcon(QtGui.QIcon(":/threshold.png"))
        # self.action_activate_threshold.setCheckable(True)
        # self.action_activate_threshold.setChecked(False)
        # self.action_activate_threshold.setToolTip("Enable/Disable Threshold")
        # self.tool_bar_analysis.addAction(self.action_activate_threshold)
        # self.threshold_label = QtGui.QLabel(" Threshold value: ", parent=self.tool_bar_analysis)
        # self.threshold_label.setEnabled(False)
        # self.tool_bar_analysis.addWidget(self.threshold_label)
        # self.threshold_spinbox = QtGui.QDoubleSpinBox(self.tool_bar_analysis)
        # self.threshold_spinbox.setMinimum(0.0)
        # self.threshold_spinbox.setMaximum(20.0)
        # self.threshold_spinbox.setSingleStep(0.01)
        # self.threshold_spinbox.setValue(1.0)
        # self.threshold_spinbox.setAccelerated(True)
        # self.threshold_spinbox.setEnabled(False)
        # self.tool_bar_analysis.addWidget(self.threshold_spinbox)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.tool_bar_analysis)

        # Add navigation toolbar
        self.tool_bar_navigation = navigationtoolbar.NavigationToolBar(self.stream_viewer.canvas, self)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.tool_bar_navigation)
        self.addToolBarBreak()

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

    def set_stream(self, stream):
        self.stream = stream
        self.stream_viewer.set_stream(self.stream)
        stream_has_any_trace = len(self.stream)
        self.centralwidget.setVisible(stream_has_any_trace)
        self.action_sta_lta.setEnabled(stream_has_any_trace)
        self.action_ampa.setEnabled(stream_has_any_trace)
        self.adjustSize()


