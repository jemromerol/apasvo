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
import matplotlib
matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

navigation_bar_items = ('Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Save', '')


class NavigationToolBar(NavigationToolbar2QTAgg):

    view_restored = QtCore.Signal()

    def __init__(self, canvas, parent=None):
        super(NavigationToolBar, self).__init__(canvas, parent)
        # remove actions not in navigation_bar_items
        self.toolitems = tuple([t for t in NavigationToolbar2QTAgg.toolitems if
                                t[0] in navigation_bar_items])
        for action in self.actions():
            if action.text() not in navigation_bar_items:
                self.removeAction(action)
            if action.text() in ('Home', 'Back', 'Forward'):
                action.triggered.connect(self.view_restored.emit)
