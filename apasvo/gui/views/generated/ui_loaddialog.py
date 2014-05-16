# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'LoadDialog.ui'
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


class Ui_LoadDialog(object):
    def setupUi(self, LoadDialog):
        LoadDialog.setObjectName("LoadDialog")
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LoadDialog.sizePolicy().hasHeightForWidth())
        LoadDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(LoadDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtGui.QGroupBox(LoadDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setAutoFillBackground(False)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.gridLayout.setSpacing(9)
        self.gridLayout.setContentsMargins(24, 12, 24, -1)
        self.gridLayout.setObjectName("gridLayout")
        self.FileFormatLabel = QtGui.QLabel(self.groupBox)
        self.FileFormatLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.FileFormatLabel.setObjectName("FileFormatLabel")
        self.gridLayout.addWidget(self.FileFormatLabel, 0, 0, 1, 1)
        self.FileFormatComboBox = QtGui.QComboBox(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.FileFormatComboBox.sizePolicy().hasHeightForWidth())
        self.FileFormatComboBox.setSizePolicy(sizePolicy)
        self.FileFormatComboBox.setObjectName("FileFormatComboBox")
        self.FileFormatComboBox.addItem("")
        self.FileFormatComboBox.addItem("")
        self.gridLayout.addWidget(self.FileFormatComboBox, 0, 1, 1, 1)
        self.DataTypeLabel = QtGui.QLabel(self.groupBox)
        self.DataTypeLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.DataTypeLabel.setObjectName("DataTypeLabel")
        self.gridLayout.addWidget(self.DataTypeLabel, 1, 0, 1, 1)
        self.DataTypeComboBox = QtGui.QComboBox(self.groupBox)
        self.DataTypeComboBox.setObjectName("DataTypeComboBox")
        self.gridLayout.addWidget(self.DataTypeComboBox, 1, 1, 1, 1)
        self.ByteOrderLabel = QtGui.QLabel(self.groupBox)
        self.ByteOrderLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.ByteOrderLabel.setObjectName("ByteOrderLabel")
        self.gridLayout.addWidget(self.ByteOrderLabel, 2, 0, 1, 1)
        self.ByteOrderComboBox = QtGui.QComboBox(self.groupBox)
        self.ByteOrderComboBox.setObjectName("ByteOrderComboBox")
        self.ByteOrderComboBox.addItem("")
        self.ByteOrderComboBox.addItem("")
        self.gridLayout.addWidget(self.ByteOrderComboBox, 2, 1, 1, 1)
        self.SampleFrequencyLabel = QtGui.QLabel(self.groupBox)
        self.SampleFrequencyLabel.setScaledContents(False)
        self.SampleFrequencyLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.SampleFrequencyLabel.setWordWrap(False)
        self.SampleFrequencyLabel.setObjectName("SampleFrequencyLabel")
        self.gridLayout.addWidget(self.SampleFrequencyLabel, 3, 0, 1, 1)
        self.SampleFrequencySpinBox = QtGui.QSpinBox(self.groupBox)
        self.SampleFrequencySpinBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.SampleFrequencySpinBox.setAccelerated(True)
        self.SampleFrequencySpinBox.setMinimum(1)
        self.SampleFrequencySpinBox.setMaximum(10000)
        self.SampleFrequencySpinBox.setProperty("value", 50)
        self.SampleFrequencySpinBox.setObjectName("SampleFrequencySpinBox")
        self.gridLayout.addWidget(self.SampleFrequencySpinBox, 3, 1, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(LoadDialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.PreviewTextEdit = QtGui.QTextEdit(self.groupBox_2)
        self.PreviewTextEdit.setReadOnly(True)
        self.PreviewTextEdit.setObjectName("PreviewTextEdit")
        self.verticalLayout_2.addWidget(self.PreviewTextEdit)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtGui.QDialogButtonBox(LoadDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(LoadDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), LoadDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), LoadDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(LoadDialog)

    def retranslateUi(self, LoadDialog):
        LoadDialog.setWindowTitle(QtGui.QApplication.translate("LoadDialog", "Load Data File As...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("LoadDialog", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.FileFormatLabel.setText(QtGui.QApplication.translate("LoadDialog", "File Format:", None, QtGui.QApplication.UnicodeUTF8))
        self.FileFormatComboBox.setItemText(0, QtGui.QApplication.translate("LoadDialog", "Binary", None, QtGui.QApplication.UnicodeUTF8))
        self.FileFormatComboBox.setItemText(1, QtGui.QApplication.translate("LoadDialog", "Text", None, QtGui.QApplication.UnicodeUTF8))
        self.DataTypeLabel.setText(QtGui.QApplication.translate("LoadDialog", "Encoding Data Type:", None, QtGui.QApplication.UnicodeUTF8))
        self.ByteOrderLabel.setText(QtGui.QApplication.translate("LoadDialog", "Byte Order:", None, QtGui.QApplication.UnicodeUTF8))
        self.ByteOrderComboBox.setItemText(0, QtGui.QApplication.translate("LoadDialog", "Little Endian (Intel)", None, QtGui.QApplication.UnicodeUTF8))
        self.ByteOrderComboBox.setItemText(1, QtGui.QApplication.translate("LoadDialog", "Big Endian (Motorola)", None, QtGui.QApplication.UnicodeUTF8))
        self.SampleFrequencyLabel.setText(QtGui.QApplication.translate("LoadDialog", "Sample Frequency (Hz):", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("LoadDialog", "Data Preview", None, QtGui.QApplication.UnicodeUTF8))

