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

from apasvo.gui.views import error


class ProcessingDialog(QtGui.QDialog):

    def __init__(self, label_text='', cancel_button_text='&Cancel',
                 cancel_label_text='Canceling...'):
        QtGui.QDialog.__init__(self)
        self.label_text = label_text
        self.cancel_button_text = cancel_button_text
        self.cancel_label_text = cancel_label_text
        self._init_ui()

    def _init_ui(self):
        self.label = QtGui.QLabel(self.label_text)
        self.pbar_widget = QtGui.QWidget(self)
        self.pbar = QtGui.QProgressBar(self.pbar_widget)
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(0)
        self.button_cancel = QtGui.QPushButton(self.cancel_button_text,
                                               self.pbar_widget)
        self.hlayout = QtGui.QHBoxLayout(self.pbar_widget)
        self.hlayout.addWidget(self.pbar)
        self.hlayout.addWidget(self.button_cancel)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.pbar_widget)
        self.button_cancel.clicked.connect(self.reject)

    def run(self, task):
        self.label.setText(self.label_text)
        self._task = task
        self._thread = QtCore.QThread(self)
        self._task.moveToThread(self._thread)
        self._thread.started.connect(self._task.run)
        self._task.finished.connect(self._thread.quit)
        self._task.finished.connect(self.accept)
        self._task.finished.connect(self._task.deleteLater)
        self._task.error.connect(self.on_error)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()
        return self.exec_()

    def set_label_text(self, label_text):
        self.label_text = label_text
        self.label.setText(self.label_text)

    def set_cancel_button_text(self, cancel_button_text):
        self.cancel_button_text = cancel_button_text
        self.button_cancel.setText(self.cancel_button_text)

    def reject(self):
        self.label.setText(self.cancel_label_text)
        self._task.abort()
        self._thread.quit()
        self._thread.wait()
        return QtGui.QDialog.reject(self)

    def on_error(self, *args, **kwargs):
        error.display_error_dlg(*args, **kwargs)
        self.reject()
