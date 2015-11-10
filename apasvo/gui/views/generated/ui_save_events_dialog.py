# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SaveDialog.ui'
#
# Created: Fri Aug 16 16:54:54 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

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

from PySide import QtCore, QtGui


class Ui_SaveEventsDialog(object):
    def setupUi(self, SaveEventsDialog):
        SaveEventsDialog.setObjectName("SaveEventsDialog")
        self.verticalLayout = QtGui.QVBoxLayout(SaveEventsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtGui.QGroupBox(SaveEventsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setAutoFillBackground(False)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.formLayout.setHorizontalSpacing(9)
        self.FileFormatLabel = QtGui.QLabel(self.groupBox)
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.FileFormatLabel)
        self.FileFormatComboBox = QtGui.QComboBox(self.groupBox)
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.FileFormatComboBox)
        self.verticalLayout.addWidget(self.groupBox)
        self.buttonBox = QtGui.QDialogButtonBox(SaveEventsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SaveEventsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SaveEventsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SaveEventsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SaveEventsDialog)

    def retranslateUi(self, SaveEventsDialog):
        SaveEventsDialog.setWindowTitle(QtGui.QApplication.translate("SaveEventsDialog", "Save Events As...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("SaveEventsDialog", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.FileFormatLabel.setText(QtGui.QApplication.translate("SaveEventsDialog", "Export File Format:", None, QtGui.QApplication.UnicodeUTF8))

