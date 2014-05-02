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

from PySide import QtCore
from PySide import QtGui

from apasvo import _version
from apasvo.gui.views.generated import qrc_icons
from apasvo.gui.views.generated import qrc_strings


class AboutDialog(QtGui.QDialog):
    """
    """

    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)
        self.setup_ui()
        self.mbutton_box.rejected.connect(self.reject)

    def setup_ui(self):
        self.main_layout = QtGui.QVBoxLayout(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(640, 480)
        # Application tab
        self.version_widget = QtGui.QWidget(self)
        self.version_icon = QtGui.QLabel(self)
        self.version_icon.setPixmap(QtGui.QPixmap(':/app.png'))
        self.version_text = QtGui.QTextEdit(self)
        self.version_text.setReadOnly(True)

        mfile = QtCore.QFile(':/version.html')
        if not mfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            self.reject()
        mversion = QtCore.QTextStream(mfile)

        self.version_text.setText(mversion.readAll())
        self.version_layout = QtGui.QVBoxLayout(self.version_widget)
        self.version_layout.addWidget(self.version_icon)
        self.version_layout.setAlignment(self.version_icon, QtCore.Qt.AlignHCenter)
        self.version_layout.addWidget(self.version_text)

        # License tab
        self.license_widget = QtGui.QWidget(self)
        self.license_layout = QtGui.QVBoxLayout(self.license_widget)
        self.license_text_edit = QtGui.QTextEdit(self)
        self.license_text_edit.setReadOnly(True)

        mfile = QtCore.QFile(':/license.txt')
        if not mfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            self.reject()
        mlicense = QtCore.QTextStream(mfile)

        self.license_text_edit.setPlainText(mlicense.readAll())
        self.license_layout.addWidget(self.license_text_edit)
        # Tab widget definition
        self.mtab_widget = QtGui.QTabWidget(self)
        self.mtab_widget.addTab(self.version_widget, u'Version')
        self.mtab_widget.addTab(self.license_widget, u'License')
        self.main_layout.addWidget(self.mtab_widget)
        # Button box
        self.mbutton_box = QtGui.QDialogButtonBox(self)
        self.mbutton_box.setOrientation(QtCore.Qt.Horizontal)
        self.mbutton_box.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.main_layout.addWidget(self.mbutton_box)


































