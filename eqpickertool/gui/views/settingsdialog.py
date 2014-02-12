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

from PySide import QtGui
from PySide import QtCore

from eqpickertool.gui.views import playertoolbar

from eqpickertool._version import _application_name
from eqpickertool._version import _organization


class SettingsDialog(QtGui.QDialog):
    """A dialog window to edit application settings.
    """

    saved = QtCore.Signal()

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setup_ui()

        self.treeWidget.currentItemChanged.connect(self._itemChanged)
        self.buttonBox.clicked.connect(self.onclick)

        self.loadSettings()

    def _itemChanged(self, current, previous):
        item_name = current.text(0)
        if item_name in self._settingsMenus:
            if self.currentMenu != self._settingsMenus[item_name]:
                self.currentMenu.setVisible(False)
                self._settingsMenus[item_name].setVisible(True)
                self.currentMenu = self._settingsMenus[item_name]

    def loadSettings(self):
        """Loads settings from persistent storage."""
        self.settings = QtCore.QSettings(_organization, _application_name)
        self.settings.beginGroup("player_settings")
        sample_rate_index = playertoolbar.sample_rates.index(int(self.settings.value('sample_rate', playertoolbar.sample_rates[0])))
        self.samplerateComboBox.setCurrentIndex(sample_rate_index)
        bit_depth_index = playertoolbar.bit_depths.index(self.settings.value('bit_depth', playertoolbar.bit_depths[0]))
        self.bitdepthComboBox.setCurrentIndex(bit_depth_index)
        self.settings.endGroup()

    def saveSettings(self):
        """Saves settings to persistent storage."""
        self.settings = QtCore.QSettings(_organization, _application_name)
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

    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtGui.QWidget(self)
        self.widget.setObjectName("widget")
        self.widget.setMinimumHeight(480)
        self.widget.setMinimumWidth(640)
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Set the settings tree widget
        self.treeWidget = QtGui.QTreeWidget(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setMinimumSize(QtCore.QSize(120, 0))
        self.treeWidget.setBaseSize(QtCore.QSize(120, 0))
        self.treeWidget.setAnimated(False)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setObjectName("treeWidget")
        item_player = QtGui.QTreeWidgetItem(self.treeWidget)
        self.horizontalLayout.addWidget(self.treeWidget)

        # Set Player Group Box
        self.playerGroupBox = QtGui.QGroupBox("Player", self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.playerGroupBox.sizePolicy().hasHeightForWidth())
        self.playerGroupBox.setSizePolicy(sizePolicy)
        self.playerGroupBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.playerGroupBox.setVisible(True)
        self.formLayout = QtGui.QFormLayout(self.playerGroupBox)
        self.formLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setRowWrapPolicy(QtGui.QFormLayout.DontWrapRows)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.formLayout.setContentsMargins(24, 24, 24, 24)
        self.formLayout.setHorizontalSpacing(9)
        self.formLayout.setVerticalSpacing(24)
        self.samplerateLabel = QtGui.QLabel("Sample rate (samples/sec.):", self.playerGroupBox)
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.samplerateLabel)
        self.samplerateComboBox = QtGui.QComboBox(self.playerGroupBox)
        self.samplerateComboBox.addItems([str(item) for item in playertoolbar.sample_rates])
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.samplerateComboBox)
        self.bitdepthLabel = QtGui.QLabel("Bit Depth:", self.playerGroupBox)
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.bitdepthLabel)
        self.bitdepthComboBox = QtGui.QComboBox(self.playerGroupBox)
        self.bitdepthComboBox.addItems([str(item) for item in playertoolbar.bit_depths])
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.bitdepthComboBox)
        self.horizontalLayout.addWidget(self.playerGroupBox)

        # Button Box
        self.verticalLayout.addWidget(self.widget)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.verticalLayout.addWidget(self.buttonBox)

        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.treeWidget.setHeaderItem(item_player)
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)

        self._settingsMenus = {}
        self._settingsMenus[self.treeWidget.topLevelItem(0).text(0)] = self.playerGroupBox
        self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(0))
        self.currentMenu = self.playerGroupBox
