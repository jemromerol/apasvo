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

from apasvo.gui.models import filterlistmodel
from apasvo.gui.delegates import dsbdelegate
from apasvo._version import _application_name
from apasvo._version import _organization


class AmpaDialog(QtGui.QDialog):
    """
    """

    def __init__(self, document, parent=None):
        super(AmpaDialog, self).__init__(parent)
        self.document = document

        self.step = 1.0 / self.document.record.fs
        self.max_value = ((len(self.document.record.signal) - 1) /  # Signal starts at t0 = 0
                          self.document.record.fs)
        self.nyquist_freq = self.document.record.fs / 2.0
        self.setup_ui()

        self._filters = filterlistmodel.FilterListModel([])
        self.filtersTable.setModel(self._filters)
        self._filters.sizeChanged.connect(self._on_size_changed)
        self._filters.dataChanged.connect(self._on_data_changed)
        filterDelegate = dsbdelegate.DoubleSpinBoxDelegate(self.filtersTable,
                                                           minimum=self.step,
                                                           maximum=self.max_value - self.step,
                                                           step=self.step)
        self.filtersTable.setItemDelegateForColumn(0, filterDelegate)

        self.ampawindowSpinBox.valueChanged.connect(self.on_ampa_window_changed)
        self.ampawindowstepSpinBox.valueChanged.connect(self.on_ampa_window_step_changed)
        self.takanamiCheckBox.toggled.connect(self.takanamiMarginLabel.setEnabled)
        self.takanamiCheckBox.toggled.connect(self.takanamiMarginSpinBox.setEnabled)
        self.startfSpinBox.valueChanged.connect(self.on_startf_changed)
        self.endfSpinBox.valueChanged.connect(self.on_endf_changed)
        self.bandwidthSpinBox.valueChanged.connect(self.on_bandwidth_changed)
        self.actionAddFilter.triggered.connect(self.addFilter)
        self.actionRemoveFilter.triggered.connect(self.removeFilter)
        model = self.filtersTable.selectionModel()
        model.selectionChanged.connect(self._on_filter_selected)
        self.buttonBox.clicked.connect(self.onclick)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.load_settings()

    def setup_ui(self):
        self.setWindowTitle("AMPA Settings")
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.setMinimumWidth(480)
        # Set AMPA General Settings Group Box
        self.ampaGeneralSettingsGroupBox = QtGui.QGroupBox("General settings", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.ampaGeneralSettingsGroupBox.sizePolicy().hasHeightForWidth())
        self.ampaGeneralSettingsGroupBox.setSizePolicy(sizePolicy)
        self.formLayout_3 = QtGui.QFormLayout(self.ampaGeneralSettingsGroupBox)
        self.formLayout_3.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout_3.setContentsMargins(12, 12, 12, 12)
        self.formLayout_3.setHorizontalSpacing(24)
        self.formLayout_3.setObjectName("formLayout_3")
        self.ampawindowLabel = QtGui.QLabel("Sliding Window Length (in seconds):", self.ampaGeneralSettingsGroupBox)
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.LabelRole, self.ampawindowLabel)
        self.ampawindowSpinBox = QtGui.QDoubleSpinBox(self.ampaGeneralSettingsGroupBox)
        self.ampawindowSpinBox.setAccelerated(True)
        self.ampawindowSpinBox.setMaximum(self.max_value)
        self.ampawindowSpinBox.setSingleStep(self.step)
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.FieldRole, self.ampawindowSpinBox)
        self.ampawindowstepLabel = QtGui.QLabel("Sliding Window Step (in seconds):", self.ampaGeneralSettingsGroupBox)
        self.formLayout_3.setWidget(1, QtGui.QFormLayout.LabelRole, self.ampawindowstepLabel)
        self.ampawindowstepSpinBox = QtGui.QDoubleSpinBox(self.ampaGeneralSettingsGroupBox)
        self.ampawindowstepSpinBox.setAccelerated(True)
        self.ampawindowstepSpinBox.setMinimum(self.step)
        self.ampawindowstepSpinBox.setSingleStep(self.step)
        self.formLayout_3.setWidget(1, QtGui.QFormLayout.FieldRole, self.ampawindowstepSpinBox)
        self.ampanoisethresholdLabel = QtGui.QLabel("Noise Threshold Percentile:", self.ampaGeneralSettingsGroupBox)
        self.formLayout_3.setWidget(2, QtGui.QFormLayout.LabelRole, self.ampanoisethresholdLabel)
        self.ampanoisethresholdSpinBox = QtGui.QSpinBox(self.ampaGeneralSettingsGroupBox)
        self.ampanoisethresholdSpinBox.setAccelerated(True)
        self.ampanoisethresholdSpinBox.setMinimum(1)
        self.formLayout_3.setWidget(2, QtGui.QFormLayout.FieldRole, self.ampanoisethresholdSpinBox)
        self.verticalLayout.addWidget(self.ampaGeneralSettingsGroupBox)

        # Set AMPA filter bank settings Group Box
        self.filterbankGroupBox = QtGui.QGroupBox("Filter Bank Settings", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.filterbankGroupBox.sizePolicy().hasHeightForWidth())
        self.filterbankGroupBox.setSizePolicy(sizePolicy)
        self.formLayout_2 = QtGui.QFormLayout(self.filterbankGroupBox)
        self.formLayout_2.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout_2.setContentsMargins(12, 12, 12, 12)
        self.formLayout_2.setHorizontalSpacing(24)
        self.startfLabel = QtGui.QLabel("Start Frequency (Hz):", self.filterbankGroupBox)
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.startfLabel)
        self.startfSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.startfSpinBox.setAccelerated(True)
        self.startfSpinBox.setMinimum(0.0)
        self.startfSpinBox.setSingleStep(0.01)
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.startfSpinBox)
        self.endfLabel = QtGui.QLabel("Max. End Frequency (Hz):", self.filterbankGroupBox)
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.endfLabel)
        self.endfSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.endfSpinBox.setAccelerated(True)
        self.endfSpinBox.setMaximum(self.nyquist_freq)
        self.endfSpinBox.setSingleStep(0.01)
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.endfSpinBox)
        self.bandwidthLabel = QtGui.QLabel("Channel Bandwidth (Hz):", self.filterbankGroupBox)
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.LabelRole, self.bandwidthLabel)
        self.bandwidthSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.bandwidthSpinBox.setAccelerated(True)
        self.bandwidthSpinBox.setMinimum(0.1)
        self.bandwidthSpinBox.setSingleStep(0.01)
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.FieldRole, self.bandwidthSpinBox)
        self.overlapLabel = QtGui.QLabel("Channel Overlap (Hz):", self.filterbankGroupBox)
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.LabelRole, self.overlapLabel)
        self.overlapSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.overlapSpinBox.setAccelerated(True)
        self.overlapSpinBox.setMinimum(0.0)
        self.overlapSpinBox.setSingleStep(0.01)
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.FieldRole, self.overlapSpinBox)
        self.verticalLayout.addWidget(self.filterbankGroupBox)

        # Set AMPA filters Group Box
        self.ampaFiltersGroupBox = QtGui.QGroupBox("Filter Lengths", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.ampaFiltersGroupBox.sizePolicy().hasHeightForWidth())
        self.ampaFiltersGroupBox.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.ampaFiltersGroupBox)
        self.verticalLayout_2.setContentsMargins(12, 12, 12, 12)

        self.ampafiltersToolBar = QtGui.QToolBar(self.ampaFiltersGroupBox)
        self.ampafiltersToolBar.setMovable(False)
        self.actionAddFilter = QtGui.QAction(self)
        self.actionAddFilter.setIcon(QtGui.QIcon(":/add.png"))
        self.actionRemoveFilter = QtGui.QAction(self)
        self.actionRemoveFilter.setIcon(QtGui.QIcon(":/remove.png"))
        self.actionRemoveFilter.setEnabled(False)
        self.ampafiltersToolBar.addAction(self.actionAddFilter)
        self.ampafiltersToolBar.addAction(self.actionRemoveFilter)

        self.filtersTable = QtGui.QTableView(self.ampaFiltersGroupBox)
        self.filtersTable.setCornerButtonEnabled(True)
        self.filtersTable.horizontalHeader().setStretchLastSection(True)
        self.filtersTable.verticalHeader().setVisible(False)
        self.filtersTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.filtersTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.filtersTable.setShowGrid(False)
        self.verticalLayout_2.addWidget(self.ampafiltersToolBar)
        self.verticalLayout_2.addWidget(self.filtersTable)
        self.verticalLayout.addWidget(self.ampaFiltersGroupBox)

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

    def on_ampa_window_changed(self, value):
        self.ampawindowstepSpinBox.setMaximum(value)

    def on_ampa_window_step_changed(self, value):
        pass

    def on_startf_changed(self, value):
        self.endfSpinBox.setMinimum(value + self.endfSpinBox.singleStep())
        self.bandwidthSpinBox.setMaximum(self.nyquist_freq - value - self.bandwidthSpinBox.singleStep())

    def on_endf_changed(self, value):
        self.startfSpinBox.setMaximum(value - self.startfSpinBox.singleStep())

    def on_bandwidth_changed(self, value):
        self.overlapSpinBox.setMaximum(value - self.overlapSpinBox.singleStep())

    def addFilter(self, value=10.0):
        self._filters.addFilter(value)
        self.ampawindowSpinBox.setMinimum(max(self._filters.list()) +
                                          self.step)

    def removeFilter(self):
        if len(self.filtersTable.selectionModel().selectedRows()) > 0:
            self._filters.removeRow(self.filtersTable.currentIndex().row())
            if self._filters.rowCount() <= 1:
                self.actionRemoveFilter.setEnabled(False)
            self.ampawindowSpinBox.setMinimum(max(self._filters.list()) +
                                              self.step)

    def load_settings(self):
        # Read settings
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("ampa_settings")
        self.ampawindowSpinBox.setValue(float(settings.value('window_len', 100.0)))
        self.ampawindowstepSpinBox.setValue(float(settings.value('overlap', 50.0)))
        self.ampanoisethresholdSpinBox.setValue(int(settings.value('noise_threshold', 90)))
        self._filters.clearFilters()
        for value in self._load_filters():
            self.addFilter(float(value))
        settings.beginGroup("filter_bank_settings")
        self.startfSpinBox.setValue(float(settings.value('startf', 2.0)))
        self.endfSpinBox.setValue(float(settings.value('endf', 12.0)))
        self.bandwidthSpinBox.setValue(float(settings.value('bandwidth', 3.0)))
        self.overlapSpinBox.setValue(float(settings.value('overlap', 1.0)))
        settings.endGroup()
        settings.endGroup()
        settings.beginGroup("takanami_settings")
        self.takanamiCheckBox.setChecked(int(settings.value('takanami', True)))
        self.takanamiMarginSpinBox.setValue(float(settings.value('takanami_margin', 5.0)))
        settings.endGroup()

    def save_settings(self):
        """Saves settings to persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup("ampa_settings")
        settings.setValue('window_len', self.ampawindowSpinBox.value())
        settings.setValue('overlap', self.ampawindowstepSpinBox.value())
        settings.setValue('step', self.ampawindowstepSpinBox.value())
        settings.setValue('noise_threshold', self.ampanoisethresholdSpinBox.value())
        settings.setValue('filters', self._filters.list())
        settings.beginGroup("filter_bank_settings")
        settings.setValue('startf', self.startfSpinBox.value())
        settings.setValue('endf', self.endfSpinBox.value())
        settings.setValue('bandwidth', self.bandwidthSpinBox.value())
        settings.setValue('overlap', self.overlapSpinBox.value())
        settings.endGroup()
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

    def _on_size_changed(self, size):
        if size <= 1:
            self.actionRemoveFilter.setEnabled(False)

    def _on_data_changed(self, top_left, bottom_right):
        self.ampawindowSpinBox.setMinimum(max(self._filters.list()))

    def _load_filters(self, default=None):
        if default is None:
            default = [30.0, 20.0, 10.0, 5.0, 2.5]
        settings = QtCore.QSettings(_organization, _application_name)
        filters = settings.value('ampa_settings/filters', default)
        if filters:
            if isinstance(filters, list):
                return list(filters)
            else:
                return [filters]
        return default

    def _on_filter_selected(self, s, d):
        self.actionRemoveFilter.setEnabled(len(self.filtersTable.selectionModel()
                                               .selectedRows()) > 0)
