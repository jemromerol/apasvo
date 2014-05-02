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


class Ui_SaveDialog(object):
    def setupUi(self, SaveDialog):
        SaveDialog.setObjectName("SaveDialog")
        self.verticalLayout = QtGui.QVBoxLayout(SaveDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.setMinimumSize(400, 200)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding,
                                                    QtGui.QSizePolicy.Policy.Expanding))
        self.groupBox = QtGui.QGroupBox(SaveDialog)
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
        self.FileFormatComboBox.addItem("")
        self.FileFormatComboBox.addItem("")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.FileFormatComboBox)
        self.DataTypeLabel = QtGui.QLabel(self.groupBox)
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.DataTypeLabel)
        self.DataTypeComboBox = QtGui.QComboBox(self.groupBox)
        self.DataTypeComboBox.addItem("")
        self.DataTypeComboBox.addItem("")
        self.DataTypeComboBox.addItem("")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.DataTypeComboBox)
        self.ByteOrderLabel = QtGui.QLabel(self.groupBox)
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.ByteOrderLabel)
        self.ByteOrderComboBox = QtGui.QComboBox(self.groupBox)
        self.ByteOrderComboBox.addItem("")
        self.ByteOrderComboBox.addItem("")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.ByteOrderComboBox)
        self.verticalLayout.addWidget(self.groupBox)
        self.buttonBox = QtGui.QDialogButtonBox(SaveDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SaveDialog)
        self.DataTypeComboBox.setCurrentIndex(2)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SaveDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SaveDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SaveDialog)

    def retranslateUi(self, SaveDialog):
        SaveDialog.setWindowTitle(QtGui.QApplication.translate("SaveDialog", "Save Characteristic Function As...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("SaveDialog", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.FileFormatLabel.setText(QtGui.QApplication.translate("SaveDialog", "File Format:", None, QtGui.QApplication.UnicodeUTF8))
        self.FileFormatComboBox.setItemText(0, QtGui.QApplication.translate("SaveDialog", "Binary", None, QtGui.QApplication.UnicodeUTF8))
        self.FileFormatComboBox.setItemText(1, QtGui.QApplication.translate("SaveDialog", "Text", None, QtGui.QApplication.UnicodeUTF8))
        self.DataTypeLabel.setText(QtGui.QApplication.translate("SaveDialog", "Encoding Data Type:", None, QtGui.QApplication.UnicodeUTF8))
        self.DataTypeComboBox.setItemText(0, QtGui.QApplication.translate("SaveDialog", "Float 16", None, QtGui.QApplication.UnicodeUTF8))
        self.DataTypeComboBox.setItemText(1, QtGui.QApplication.translate("SaveDialog", "Float 32", None, QtGui.QApplication.UnicodeUTF8))
        self.DataTypeComboBox.setItemText(2, QtGui.QApplication.translate("SaveDialog", "Float 64", None, QtGui.QApplication.UnicodeUTF8))
        self.ByteOrderLabel.setText(QtGui.QApplication.translate("SaveDialog", "Byte Order:", None, QtGui.QApplication.UnicodeUTF8))
        self.ByteOrderComboBox.setItemText(0, QtGui.QApplication.translate("SaveDialog", "Little Endian (Intel)", None, QtGui.QApplication.UnicodeUTF8))
        self.ByteOrderComboBox.setItemText(1, QtGui.QApplication.translate("SaveDialog", "Big Endian (Motorola)", None, QtGui.QApplication.UnicodeUTF8))

