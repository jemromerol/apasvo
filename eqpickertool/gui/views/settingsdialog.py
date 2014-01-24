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

from PySide import QtGui, QtCore

from eqpickertool.gui.views.converted import ui_settingsdialog
from eqpickertool.gui.models import filterlistmodel
from eqpickertool.gui.delegates import dsbdelegate
from eqpickertool.gui.views import playertoolbar

from eqpickertool._version import _application_name
from eqpickertool._version import _organization


class SettingsDialog(QtGui.QDialog, ui_settingsdialog.Ui_SettingsDialog):
    """A dialog window to edit application settings.
    """

    saved = QtCore.Signal()

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)

        self._filters = filterlistmodel.FilterListModel([])
        self.filtersTable.setModel(self._filters)
        self._filters.sizeChanged.connect(self._onSizeChanged)
        filterDelegate = dsbdelegate.DoubleSpinBoxDelegate(self.filtersTable)
        self.filtersTable.setItemDelegateForColumn(0, filterDelegate)

        self.treeWidget.currentItemChanged.connect(self._itemChanged)
        self.staSpinBox.valueChanged.connect(self._staChanged)
        self.ltaSpinBox.valueChanged.connect(self._ltaChanged)
        self.takanamiCheckBox.toggled.connect(self.takanamiMarginLabel.setEnabled)
        self.takanamiCheckBox.toggled.connect(self.takanamiMarginSpinBox.setEnabled)
        self.startfSpinBox.valueChanged.connect(self._startfChanged)
        self.endfSpinBox.valueChanged.connect(self._endfChanged)
        self.bandwidthSpinBox.valueChanged.connect(self._bandwidthChanged)
        self.actionAddFilter.triggered.connect(self.addFilter)
        self.actionRemoveFilter.triggered.connect(self.removeFilter)
        self.buttonBox.clicked.connect(self.onclick)

        self.loadSettings()

    def _onSizeChanged(self, size):
        if size <= 1:
            self.actionRemoveFilter.setEnabled(False)
        else:
            self.actionRemoveFilter.setEnabled(True)

    def _itemChanged(self, current, previous):
        item_name = current.text(0)
        if item_name in self._settingsMenus:
            if self.currentMenu != self._settingsMenus[item_name]:
                self.currentMenu.setVisible(False)
                self._settingsMenus[item_name].setVisible(True)
                self.currentMenu = self._settingsMenus[item_name]

    def _staChanged(self, value):
        self.ltaSpinBox.setMinimum(value + self.ltaSpinBox.singleStep())

    def _ltaChanged(self, value):
        self.staSpinBox.setMaximum(value - self.staSpinBox.singleStep())

    def _startfChanged(self, value):
        self.endfSpinBox.setMinimum(value + self.endfSpinBox.singleStep())

    def _endfChanged(self, value):
        self.startfSpinBox.setMaximum(value - self.startfSpinBox.singleStep())

    def _bandwidthChanged(self, value):
        self.overlapSpinBox.setMaximum(value - self.overlapSpinBox.singleStep())

    def addFilter(self, value=10.0):
        self._filters.addFilter(value)

    def removeFilter(self):
        self._filters.removeRow(self.filtersTable.currentIndex().row())
        if self._filters.rowCount() <= 1:
            self.actionRemoveFilter.setEnabled(False)

    def loadSettings(self):
        """Loads settings from persistent storage."""
        self.settings = QtCore.QSettings(_organization, _application_name)
        self.settings.beginGroup("stalta_settings")
        self.staSpinBox.setValue(float(self.settings.value('sta_window_len', 5.0)))
        self.ltaSpinBox.setValue(float(self.settings.value('lta_window_len', 100.0)))
        self.settings.endGroup()
        self.settings.beginGroup("ampa_settings")
        self.ampawindowSpinBox.setValue(float(self.settings.value('window_len', 100.0)))
        self.ampawindowstepSpinBox.setValue(float(self.settings.value('overlap', 50.0)))
        self.ampanoisethresholdSpinBox.setValue(int(self.settings.value('noise_threshold', 90)))
        for value in self._load_filters():
            self._filters.addFilter(float(value))
        self.settings.beginGroup("filter_bank_settings")
        self.startfSpinBox.setValue(float(self.settings.value('startf', 2.0)))
        self.endfSpinBox.setValue(float(self.settings.value('endf', 12.0)))
        self.bandwidthSpinBox.setValue(float(self.settings.value('bandwidth', 3.0)))
        self.overlapSpinBox.setValue(float(self.settings.value('overlap', 1.0)))
        self.settings.endGroup()
        self.settings.endGroup()
        self.settings.beginGroup("takanami_settings")
        self.takanamiCheckBox.setChecked(int(self.settings.value('takanami', True)))
        self.takanamiMarginSpinBox.setValue(float(self.settings.value('takanami_margin', 5.0)))
        self.settings.endGroup()
        self.settings.beginGroup("player_settings")
        sample_rate_index = playertoolbar.sample_rates.index(int(self.settings.value('sample_rate', playertoolbar.sample_rates[0])))
        self.samplerateComboBox.setCurrentIndex(sample_rate_index)
        bit_depth_index = playertoolbar.bit_depths.index(self.settings.value('bit_depth', playertoolbar.bit_depths[0]))
        self.bitdepthComboBox.setCurrentIndex(bit_depth_index)
        self.settings.endGroup()

    def saveSettings(self):
        """Saves settings to persistent storage."""
        self.settings = QtCore.QSettings(_organization, _application_name)
        self.settings.beginGroup("stalta_settings")
        self.settings.setValue('sta_window_len', self.staSpinBox.value())
        self.settings.setValue('lta_window_len', self.ltaSpinBox.value())
        self.settings.endGroup()
        self.settings.beginGroup("ampa_settings")
        self.settings.setValue('window_len', self.ampawindowSpinBox.value())
        self.settings.setValue('step', self.ampawindowstepSpinBox.value())
        self.settings.setValue('noise_threshold', self.ampanoisethresholdSpinBox.value())
        self.settings.setValue('filters', self._filters.list())
        self.settings.beginGroup("filter_bank_settings")
        self.settings.setValue('startf', self.startfSpinBox.value())
        self.settings.setValue('endf', self.endfSpinBox.value())
        self.settings.setValue('bandwidth', self.bandwidthSpinBox.value())
        self.settings.setValue('overlap', self.overlapSpinBox.value())
        self.settings.endGroup()
        self.settings.endGroup()
        self.settings.beginGroup("takanami_settings")
        self.settings.setValue('takanami', self.takanamiCheckBox.checkState())
        self.settings.setValue('takanami_margin', self.takanamiMarginSpinBox.value())
        self.settings.endGroup()
        self.settings.beginGroup("player_settings")
        self.settings.setValue('sample_rate', self.samplerateComboBox.currentText())
        self.settings.setValue('bit_depth', self.bitdepthComboBox.currentText())
        self.settings.endGroup()
        self.saved.emit()

    def onclick(self, button):
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Apply:
            self.saveSettings()
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Ok:
            self.saveSettings()

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
