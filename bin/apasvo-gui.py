#!/usr/bin/python2.7
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

import sys
from PySide import QtGui, QtCore

from apasvo._version import _application_name
from apasvo.gui.views import mainwindow


if __name__ == '__main__':
#    QtGui.QApplication.setLibraryPaths([])  # Disable looking for plugins
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(_application_name)
    app.setWindowIcon(QtGui.QIcon(":/app.png"))

    # Create and display the splash screen
    splash = QtGui.QSplashScreen(QtGui.QPixmap(":splash.png"), QtCore.Qt.WindowStaysOnTopHint)
    splash.show()

    # Load libraries
    splash.showMessage("Loading libraries...")
    import matplotlib
    matplotlib.rcParams['backend'] = 'qt4agg'
    matplotlib.rcParams['backend.qt4'] = 'PySide'
    matplotlib.rcParams['patch.antialiased'] = False
    matplotlib.rcParams['agg.path.chunksize'] = 80000

    import numpy as np
    import traceback
    from apasvo.gui.views.generated import qrc_icons
    from apasvo.gui.delegates import cbdelegate
    from apasvo.gui.models import eventlistmodel
    from apasvo.gui.models import pickingtask
    from apasvo.gui.views import aboutdialog
    from apasvo.gui.views import svwidget
    from apasvo.gui.views import navigationtoolbar
    from apasvo.gui.views import loaddialog
    from apasvo.gui.views import savedialog
    from apasvo.gui.views import save_events_dialog
    from apasvo.gui.views import settingsdialog
    from apasvo.gui.views import takanamidialog
    from apasvo.gui.views import staltadialog
    from apasvo.gui.views import ampadialog
    from apasvo.gui.views import playertoolbar
    from apasvo.gui.views import error

    from apasvo.picking import stalta
    from apasvo.picking import ampa
    from apasvo.picking import apasvotrace as rc

    app.processEvents()

    # Create and display the main window
    main = mainwindow.MainWindow()
    main.show()
    splash.finish(main)

    try:
        app.exec_()
    except Exception, e:
        error.display_error_dlg(str(e), traceback.format_exc())
        sys.exit(1)
    sys.exit(0)
