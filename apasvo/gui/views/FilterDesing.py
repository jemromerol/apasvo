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
from scipy import signal
from scipy.signal import butter, lfilter, freqz

import numpy as np
import traceback
from apasvo.picking import apasvotrace as rc
from apasvo.picking import takanami
from apasvo._version import _application_name
from apasvo._version import _organization

MINIMUM_MARGIN_IN_SECS = 0.5


class FilterDesignTask(QtCore.QObject):
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
        super(FilterDesignTask, self).__init__()
        self.record = record


class FilterDesignDialog(QtGui.QDialog):
    """A dialog to apply Takanami's AR picking method to a selected piece of a
    seismic signal.

    Attributes:
        document: Current opened document containing a seismic record.
        seismic_event: A seismic event to be refined by using Takanami method.
            If no event is provided, then a new seismic event will be created
            by using the estimated arrival time after clicking on 'Accept'
    """

    def __init__(self, stream,trace_list=None,seismic_event=None, parent=None):
        super(FilterDesignDialog, self).__init__(parent)


        traces = stream.traces if not trace_list else trace_list

        self.nyquist_freq = max([trace.fs for trace in traces]) / 2.0

        #self.document = document

        #self.record = self.document.record
        #self.nyquist_freq = self.record.fs/2.0;

        #self.load_settings()

        #self.seismic_event = seismic_event



        self._init_ui()

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.clicked.connect(self.on_click)

    def _init_ui(self):
        self.setWindowTitle("Filter Design (Butterworth-Bandpass Filter)")
        self.fig, _ = plt.subplots(1, 1, sharex=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumSize(self.canvas.size())
        self.canvas.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding,
                                                    QtGui.QSizePolicy.Policy.Expanding))
        self.toolBarNavigation = navigationtoolbar.NavigationToolBar(self.canvas, self)
        self.position_label = QtGui.QLabel("Frequency Response")
        self.group_box = QtGui.QGroupBox(self)
        self.group_box2 = QtGui.QGroupBox(self)
        self.group_box3 = QtGui.QGroupBox(self)
        self.group_box.setTitle("")
        self.group_box2.setTitle("")
        self.group_box3.setTitle("Parameters")
        self.start_point_label = QtGui.QLabel("Min. Frequency (Hz): ")
        self.start_point_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))

        self.start_point_spinbox = QtGui.QDoubleSpinBox(self.group_box)
        self.start_point_spinbox.setMinimum(0.0)
        self.start_point_spinbox.setSingleStep(1.00)
        self.start_point_spinbox.setAccelerated(True)
        self.start_point_spinbox.setMaximum(self.nyquist_freq-5)
        self.end_point_label = QtGui.QLabel("Max. Frequency (Hz):")
        self.end_point_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))
        self.end_point_spinbox = QtGui.QDoubleSpinBox(self.group_box)
        self.end_point_spinbox.setMinimum(0.0)
        self.end_point_spinbox.setSingleStep(1.00)
        self.end_point_spinbox.setAccelerated(True)
        self.end_point_spinbox.setMaximum(self.nyquist_freq)
        self.end_point_spinbox.setValue(5.0)
        #######################################################################

        self.number_coefficient_label = QtGui.QLabel("Order: ")
        self.number_coefficient_label2 = QtGui.QLabel("")
        self.number_coefficient_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))
        self.number_coefficient_label2.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Maximum,
                                                               QtGui.QSizePolicy.Policy.Preferred))
        self.number_coefficient_spinbox = QtGui.QDoubleSpinBox(self.group_box2)
        self.number_coefficient_spinbox.adjustSize()
        self.number_coefficient_spinbox.setMinimum(1.0)
        self.number_coefficient_spinbox.setSingleStep(1.00)
        self.number_coefficient_spinbox.setAccelerated(True)
        self.zeroPhaseCheckBox = QtGui.QCheckBox("Apply Zero Phase on results", self.group_box2)
        self.zeroPhaseCheckBox.setChecked(True)

        #######################################################################

        self.group_box_layout = QtGui.QHBoxLayout(self.group_box)
        self.group_box_layout.setContentsMargins(9, 9, 9, 9)
        self.group_box_layout.setSpacing(12)
        self.group_box_layout.addWidget(self.start_point_label)
        self.group_box_layout.addWidget(self.start_point_spinbox)
        self.group_box_layout.addWidget(self.end_point_label)
        self.group_box_layout.addWidget(self.end_point_spinbox)
        #####################################################################
        self.group_box2_layout = QtGui.QHBoxLayout(self.group_box2)
        self.group_box2_layout.setContentsMargins(9, 9, 9, 9)
        self.group_box2_layout.setSpacing(12)
        self.group_box2_layout.addWidget(self.zeroPhaseCheckBox)
        ###################################################################
        self.group_box3_layout = QtGui.QHBoxLayout(self.group_box3)
        self.group_box3_layout.setContentsMargins(9, 9, 9, 9)
        self.group_box3_layout.setSpacing(12)
        self.group_box3_layout.addWidget(self.number_coefficient_label)
        self.group_box3_layout.addWidget(self.number_coefficient_spinbox)
        self.group_box3_layout.addWidget(self.number_coefficient_label2)
        #####################################################################
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
        self.layout.addWidget(self.group_box3)
        self.layout.addWidget(self.group_box)
        self.layout.addWidget(self.group_box2)
        self.layout.addWidget(self.button_box)

    def on_click(self, button):
        if self.button_box.standardButton(button) == QtGui.QDialogButtonBox.Ok:
            self.load_settings()
        if self.button_box.standardButton(button) == QtGui.QDialogButtonBox.Apply:
            self.do_filter_response()


    def load_settings(self):
        """Loads settings from persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("filterdesign_settings")
        #self.default_margin = int(float(settings.value('filterdesign_margin', 5.0)) *
                             #self.record.fs)
        settings.setValue('freq_min', self.start_point_spinbox.value())
        settings.setValue('freq_max', self.end_point_spinbox.value())
        settings.setValue('coef_number', self.number_coefficient_spinbox.value())
        settings.setValue('zero_phase', self.zeroPhaseCheckBox.isChecked())
        settings.endGroup()

    def butter_bandpass(self,lowcut, highcut, fs, order=5):
        nyq = 0.5 * self.nyquist_freq
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a


    def butter_bandpass_filter(self,data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        y = lfilter(b, a, data)
        return y

    def do_filter_response(self):

        b, a = self.butter_bandpass(self.start_point_spinbox.value(), self.end_point_spinbox.value(), self.nyquist_freq, order=self.number_coefficient_spinbox.value())
        w, h = freqz(b, a)
        ax = self.fig.axes[0]
        ax2 = ax.twinx()
        ax.cla()
        ax2.cla()
        ax.plot(w, 20*np.log10(abs(h)),'b',rasterized=True)[0]
        ax.set_title('Digital filter frequency response (Butterworth-Bandpass filter)')
        ax.set_xlabel('Frequency [rad/sample]')
        ax.set_ylabel('Amplitude [dB]', color='b')
        angles = np.unwrap(np.angle(h))
        ax.axis('tight')
        ax.grid(which='both', axis='both')
        ax2.plot(w, angles, 'g')
        ax2.set_ylabel('Angle (radians)', color='g')
        self.canvas.draw_idle()
