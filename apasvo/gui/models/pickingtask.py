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

import traceback
from apasvo._version import _application_name
from apasvo._version import _organization


class PickingTask(QtCore.QObject):
    """A class to handle an event picking/detection task.

    PickingTask objects are meant to be passed to a QThread instance
    that controls their execution.

    """

    finished = QtCore.Signal()
    error = QtCore.Signal(str, str)

    def __init__(self, document, alg, threshold=None):
        super(PickingTask, self).__init__()
        self.document = document
        self.alg = alg
        self.threshold = threshold

    def run(self):
        settings = QtCore.QSettings(_organization, _application_name)
        takanami = int(settings.value('takanami_settings/takanami', False))
        takanami_margin = float(settings.value('takanami_margin', 5.0))
        try:
            self.document.detectEvents(self.alg, threshold=self.threshold,
                               takanami=takanami,
                               takanami_margin=takanami_margin)
        except Exception, e:
            self.error.emit(str(e), traceback.format_exc())
        self.finished.emit()

    def abort(self):
        pass
