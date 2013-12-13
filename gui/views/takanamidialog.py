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


class TakanamiDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(TakanamiDialog, self).__init__(parent)
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("Takanami's Autoregressive Method")
        self.fig, _ = plt.subplots(2, 1, sharex=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumSize(self.canvas.size())
        self.position_label = QtGui.QLabel("Time: 00:00:00.000  CF value: 0.000")
        self.group_box = QtGui.QGroupBox(self)
        self.group_box.setTitle("Maximum margins")
