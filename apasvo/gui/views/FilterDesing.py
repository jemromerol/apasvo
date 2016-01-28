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


class FilterDesingTask(QtCore.QObject):
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

    def __init__(self, record):
        super(FilterDesingTask, self).__init__()
        self.record = record


class FilterDesingDialog(QtGui.QDialog):
    """A dialog to apply Takanami's AR picking method to a selected piece of a
    seismic signal.

    Attributes:
        document: Current opened document containing a seismic record.
        seismic_event: A seismic event to be refined by using Takanami method.
            If no event is provided, then a new seismic event will be created
            by using the estimated arrival time after clicking on 'Accept'
    """

    def __init__(self, stream, document,trace_list=None,seismic_event=None, parent=None):
        super(FilterDesingDialog, self).__init__(parent)


        traces = stream.traces if not trace_list else trace_list

        self.nyquist_freq = max([trace.fs for trace in traces]) / 2.0
        self.document = document
        self.record = self.document.record
        #self.nyquist_freq = self.record.fs/2.0;
        self.load_settings()

        self.seismic_event = seismic_event



        self._init_ui()

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.clicked.connect(self.on_click)
        #self.start_point_spinbox.timeChanged.connect(self.on_start_point_changed)
        #self.end_point_spinbox.timeChanged.connect(self.on_end_point_changed)

    def _init_ui(self):
        self.setWindowTitle("Filters Desing")
        self.fig, _ = plt.subplots(1, 1, sharex=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumSize(self.canvas.size())
        self.canvas.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding,
                                                    QtGui.QSizePolicy.Policy.Expanding))
        self.toolBarNavigation = navigationtoolbar.NavigationToolBar(self.canvas, self)
        self.position_label = QtGui.QLabel("Frequency Response")
        self.group_box = QtGui.QGroupBox(self)
        self.group_box.setTitle("Limits")
        self.start_point_label = QtGui.QLabel("Start Frequency (Hz): ")
        self.start_point_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))

        self.start_point_spinbox = QtGui.QDoubleSpinBox(self.group_box)
        self.start_point_spinbox.setMinimum(0.0)
        self.start_point_spinbox.setSingleStep(1.00)
        self.start_point_spinbox.setAccelerated(True)
        self.start_point_spinbox.setMaximum(self.nyquist_freq-5)
        self.end_point_label = QtGui.QLabel("Max. End Frequency (Hz):")
        self.end_point_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))
        self.end_point_spinbox = QtGui.QDoubleSpinBox(self.group_box)
        self.end_point_spinbox.setMinimum(0.0)
        self.end_point_spinbox.setSingleStep(1.00)
        self.end_point_spinbox.setAccelerated(True)
        self.end_point_spinbox.setMaximum(self.nyquist_freq)
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

    def on_click(self, button):
        if self.button_box.standardButton(button) == QtGui.QDialogButtonBox.Ok:
            self.save_event()
        if self.button_box.standardButton(button) == QtGui.QDialogButtonBox.Apply:
            self.do_takanami()


    def on_position_estimated(self, time, aic, n0_aic):
        self.event_time = time
        time_in_secs = self.event_time / self.record.fs
        self.position_label.setText("Estimated Arrival Time: {}".format(
            clt.float_secs_2_string_date(time_in_secs, starttime=self.record.starttime)))
        # Plot estimated arrival time
        m_event = rc.ApasvoEvent(self.record, time, aic=aic, n0_aic=n0_aic)
        m_event.plot_aic(show_envelope=True, num=self.fig.number)
        self.fig.canvas.draw_idle()

    def load_settings(self):
        """Loads settings from persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("filterdesing_settings")
        self.default_margin = int(float(settings.value('filterdesing_margin', 5.0)) *
                             self.record.fs)
        settings.endGroup()

    def save_event(self):
        """"""
        if self.seismic_event is not None:
            if self.seismic_event.stime != self.event_time:
                self.document.editEvent(self.seismic_event,
                                        stime=self.event_time,
                                        method=rc.method_takanami,
                                        evaluation_mode=rc.mode_automatic,
                                        evaluation_status=rc.status_preliminary)
        else:
            self.document.createEvent(self.event_time,
                                      method=rc.method_takanami,
                                      evaluation_mode=rc.mode_automatic,
                                      evaluation_status=rc.status_preliminary)


