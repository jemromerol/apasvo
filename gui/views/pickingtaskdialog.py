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

from PySide import QtGui, QtCore

from _version import _application_name
from _version import _organization


class PickingTask(QtCore.QObject):
    """A class to handle an event picking/detection task.

    PickingTask objects are meant to be passed to a QThread instance
    that controls their execution.
    """

    finished = QtCore.Signal()

    def __init__(self, record, alg, threshold=None):
        super(PickingTask, self).__init__()
        self.record = record
        self.alg = alg
        self.threshold = threshold

    def run(self):
        settings = QtCore.QSettings(_organization, _application_name)
        takanami = int(settings.value('takanami_settings/takanami', False))
        takanami_margin = float(settings.value('takanami_margin', 5.0))
        self.record.detect(self.alg, threshold=self.threshold,
                           takanami=takanami,
                           takanami_margin=takanami_margin)
        self.finished.emit()


class PickingTaskDialog(QtGui.QDialog):
    """A progress dialog window to provide feedback to the user while
    an event detection/picking task is being performed.

    Attributes:
        record: Current opened seismic document, picking.Record object.
        alg: A detection/picking algorithm object, e. g. a
            picking.ampa.Ampa or picking.stalta.StaLta instance.
        threshold: Local maxima found in the characteristic function above
            this value will be returned by the function as possible events
            (detection mode).
            If threshold is None, the function will return only the global
            maximum (picking mode).
            Default value is None.
    """

    def __init__(self, record, alg, threshold=None):
        QtGui.QDialog.__init__(self)
        self.record = record
        self._events = self.record.events
        self.alg = alg
        self.threshold = threshold
        self.init_ui()

        self._thread = QtCore.QThread(self)
        self._task = PickingTask(self.record, self.alg, self.threshold)
        self._task.moveToThread(self._thread)
        self._thread.started.connect(self._task.run)
        self._task.finished.connect(self._thread.quit)
        self._task.finished.connect(self.accept)
        self._task.finished.connect(self._task.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def init_ui(self):
        self.setWindowTitle('Signal processing')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.label = QtGui.QLabel("Applying %s..." % self.alg._name, self)
        self.pbarWidget = QtGui.QWidget(self)
        self.pbar = QtGui.QProgressBar(self.pbarWidget)
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(0)
        #self.button_cancel = QtGui.QPushButton('&Cancel', self.pbarWidget)
        self.hlayout = QtGui.QHBoxLayout(self.pbarWidget)
        self.hlayout.addWidget(self.pbar)
        #self.hlayout.addWidget(self.button_cancel)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.pbarWidget)
        #self.button_cancel.clicked.connect(self.reject)

    def reject(self):
        self._thread.terminate()
        self._thread.wait()
        self.record.events = self._events
        return QtGui.QDialog.reject(self)
