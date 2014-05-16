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

from apasvo._version import _application_name
from apasvo._version import _organization


class StaLtaDialog(QtGui.QDialog):
    """
    """

    def __init__(self, document, parent=None):
        super(StaLtaDialog, self).__init__(parent)
        self.document = document

        self.step = 1.0 / self.document.record.fs
        self.max_value = ((len(self.document.record.signal) - 1) /  # Signal starts at t0 = 0
                          self.document.record.fs)

        self.setup_ui()

        self.staSpinBox.valueChanged.connect(self.on_sta_changed)
        self.ltaSpinBox.valueChanged.connect(self.on_lta_changed)
        self.takanamiCheckBox.toggled.connect(self.takanamiMarginLabel.setEnabled)
        self.takanamiCheckBox.toggled.connect(self.takanamiMarginSpinBox.setEnabled)
        self.buttonBox.clicked.connect(self.onclick)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.load_settings()

    def setup_ui(self):
        self.setWindowTitle("STA-LTA settings")
        self.verticalLayout = QtGui.QVBoxLayout(self)
        # Set STA-LTA Group Box
        self.staltaGroupBox = QtGui.QGroupBox("STA-LTA", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.staltaGroupBox.sizePolicy().hasHeightForWidth())
        self.staltaGroupBox.setSizePolicy(sizePolicy)
        self.staltaGroupBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.formLayout = QtGui.QFormLayout(self.staltaGroupBox)
        self.formLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setRowWrapPolicy(QtGui.QFormLayout.DontWrapRows)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.formLayout.setContentsMargins(12, 12, 12, 12)
        self.formLayout.setHorizontalSpacing(24)
        self.staLabel = QtGui.QLabel("STA window (in seconds):", self.staltaGroupBox)
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.staLabel)
        self.staSpinBox = QtGui.QDoubleSpinBox(self.staltaGroupBox)
        self.staSpinBox.setAccelerated(True)
        self.staSpinBox.setMinimum(self.step)
        self.staSpinBox.setSingleStep(self.step)
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.staSpinBox)
        self.ltaLabel = QtGui.QLabel("LTA window (in seconds):", self.staltaGroupBox)
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.ltaLabel)
        self.ltaSpinBox = QtGui.QDoubleSpinBox(self.staltaGroupBox)
        self.ltaSpinBox.setAccelerated(True)
        self.ltaSpinBox.setMaximum(self.max_value)
        self.ltaSpinBox.setSingleStep(self.step)
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.ltaSpinBox)
        self.verticalLayout.addWidget(self.staltaGroupBox)

        # Set Takanami Group Box
        self.takanamiGroupBox = QtGui.QGroupBox("Takanami Settings", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.takanamiGroupBox.sizePolicy().hasHeightForWidth())
        self.takanamiGroupBox.setSizePolicy(sizePolicy)
        self.takanamiformLayout = QtGui.QFormLayout(self.takanamiGroupBox)
        self.takanamiformLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.takanamiformLayout.setContentsMargins(12, 12, 12, 12)
        self.takanamiformLayout.setHorizontalSpacing(24)
        self.takanamiCheckBox = QtGui.QCheckBox("Apply Takanami on results", self.takanamiGroupBox)
        self.takanamiCheckBox.setChecked(True)
        self.takanamiformLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.takanamiCheckBox)
        self.takanamiMarginLabel = QtGui.QLabel("Takanami Max. Margin (in seconds):", self.takanamiGroupBox)
        self.takanamiformLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.takanamiMarginLabel)
        self.takanamiMarginSpinBox = QtGui.QDoubleSpinBox(self.takanamiGroupBox)
        self.takanamiMarginSpinBox.setAccelerated(True)
        self.takanamiMarginSpinBox.setMinimum(1.0)
        self.takanamiMarginSpinBox.setMaximum(20.0)
        self.takanamiMarginSpinBox.setSingleStep(self.step)
        self.takanamiformLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.takanamiMarginSpinBox)
        self.verticalLayout.addWidget(self.takanamiGroupBox)

        # Button Box
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.RestoreDefaults |
                                          QtGui.QDialogButtonBox.Cancel |
                                          QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

    def on_sta_changed(self, value):
        self.ltaSpinBox.setMinimum(value + self.step)

    def on_lta_changed(self, value):
        self.staSpinBox.setMaximum(value - self.step)

    def load_settings(self):
        # Read settings
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup('stalta_settings')
        self.staSpinBox.setValue(float(settings.value('sta_window_len', 5.0)))
        self.ltaSpinBox.setValue(float(settings.value('lta_window_len', 100.0)))
        settings.endGroup()
        settings.beginGroup("takanami_settings")
        self.takanamiCheckBox.setChecked(int(settings.value('takanami', True)))
        self.takanamiMarginSpinBox.setValue(float(settings.value('takanami_margin', 5.0)))
        settings.endGroup()

    def save_settings(self):
        """Saves settings to persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("stalta_settings")
        settings.setValue('sta_window_len', self.staSpinBox.value())
        settings.setValue('lta_window_len', self.ltaSpinBox.value())
        settings.endGroup()
        settings.beginGroup("takanami_settings")
        settings.setValue('takanami', self.takanamiCheckBox.checkState())
        settings.setValue('takanami_margin', self.takanamiMarginSpinBox.value())
        settings.endGroup()

    def onclick(self, button):
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.RestoreDefaults:
            self.load_settings()
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Apply:
            self.save_settings()
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Ok:
            self.save_settings()




















