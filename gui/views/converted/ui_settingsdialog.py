# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SettingsDialog.ui'
#
# Created: Thu Aug 29 12:08:19 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

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

from PySide import QtCore, QtGui
from gui.views import playertoolbar


class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        self.verticalLayout = QtGui.QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtGui.QWidget(SettingsDialog)
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
        item_stalta = QtGui.QTreeWidgetItem(self.treeWidget)
        item_ampa = QtGui.QTreeWidgetItem(self.treeWidget)
        item_ampa_general = QtGui.QTreeWidgetItem(item_ampa)
        item_ampa_fb = QtGui.QTreeWidgetItem(item_ampa)
        item_ampa_filters = QtGui.QTreeWidgetItem(item_ampa)
        item_takanami = QtGui.QTreeWidgetItem(self.treeWidget)
        item_player = QtGui.QTreeWidgetItem(self.treeWidget)
        self.horizontalLayout.addWidget(self.treeWidget)

        # Set STA-LTA Group Box
        self.staltaGroupBox = QtGui.QGroupBox(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.staltaGroupBox.sizePolicy().hasHeightForWidth())
        self.staltaGroupBox.setSizePolicy(sizePolicy)
        self.staltaGroupBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.staltaGroupBox.setObjectName("staltaGroupBox")
        self.staltaGroupBox.setVisible(True)
        self.formLayout = QtGui.QFormLayout(self.staltaGroupBox)
        self.formLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setRowWrapPolicy(QtGui.QFormLayout.DontWrapRows)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.formLayout.setContentsMargins(24, 24, 24, 24)
        self.formLayout.setHorizontalSpacing(9)
        self.formLayout.setVerticalSpacing(24)
        self.formLayout.setObjectName("formLayout")
        self.staLabel = QtGui.QLabel(self.staltaGroupBox)
        self.staLabel.setObjectName("staLabel")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.staLabel)
        self.staSpinBox = QtGui.QDoubleSpinBox(self.staltaGroupBox)
        self.staSpinBox.setAccelerated(True)
        self.staSpinBox.setMinimum(0.5)
        self.staSpinBox.setMaximum(100.0)
        self.staSpinBox.setSingleStep(0.01)
        self.staSpinBox.setProperty("value", 5.0)
        self.staSpinBox.setObjectName("staSpinBox")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.staSpinBox)
        self.ltaLabel = QtGui.QLabel(self.staltaGroupBox)
        self.ltaLabel.setObjectName("ltaLabel")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.ltaLabel)
        self.ltaSpinBox = QtGui.QDoubleSpinBox(self.staltaGroupBox)
        self.ltaSpinBox.setWrapping(False)
        self.ltaSpinBox.setAccelerated(True)
        self.ltaSpinBox.setMinimum(5.0)
        self.ltaSpinBox.setMaximum(1000.0)
        self.ltaSpinBox.setSingleStep(0.01)
        self.ltaSpinBox.setProperty("value", 100.0)
        self.ltaSpinBox.setObjectName("ltaSpinBox")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.ltaSpinBox)
        self.horizontalLayout.addWidget(self.staltaGroupBox)

        # Set AMPA General Settings Group Box
        self.ampaGeneralSettingsGroupBox = QtGui.QGroupBox(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.ampaGeneralSettingsGroupBox.sizePolicy().hasHeightForWidth())
        self.ampaGeneralSettingsGroupBox.setSizePolicy(sizePolicy)
        self.ampaGeneralSettingsGroupBox.setObjectName("ampaGeneralSettingsGroupBox")
        self.ampaGeneralSettingsGroupBox.setVisible(False)
        self.formLayout_3 = QtGui.QFormLayout(self.ampaGeneralSettingsGroupBox)
        self.formLayout_3.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout_3.setContentsMargins(24, 24, 24, 24)
        self.formLayout_3.setVerticalSpacing(24)
        self.formLayout_3.setObjectName("formLayout_3")
        self.ampawindowLabel = QtGui.QLabel(self.ampaGeneralSettingsGroupBox)
        self.ampawindowLabel.setObjectName("ampawindowLabel")
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.LabelRole, self.ampawindowLabel)
        self.ampawindowSpinBox = QtGui.QDoubleSpinBox(self.ampaGeneralSettingsGroupBox)
        self.ampawindowSpinBox.setAccelerated(True)
        self.ampawindowSpinBox.setMaximum(1000.0)
        self.ampawindowSpinBox.setSingleStep(0.01)
        self.ampawindowSpinBox.setProperty("value", 100.0)
        self.ampawindowSpinBox.setObjectName("ampawindowSpinBox")
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.FieldRole, self.ampawindowSpinBox)
        self.ampawindowstepLabel = QtGui.QLabel(self.ampaGeneralSettingsGroupBox)
        self.ampawindowstepLabel.setObjectName("ampawindowstepLabel")
        self.formLayout_3.setWidget(1, QtGui.QFormLayout.LabelRole, self.ampawindowstepLabel)
        self.ampawindowstepSpinBox = QtGui.QDoubleSpinBox(self.ampaGeneralSettingsGroupBox)
        self.ampawindowstepSpinBox.setAccelerated(True)
        self.ampawindowstepSpinBox.setMaximum(1000.0)
        self.ampawindowstepSpinBox.setSingleStep(0.01)
        self.ampawindowstepSpinBox.setProperty("value", 50.0)
        self.ampawindowstepSpinBox.setObjectName("ampawindowstepSpinBox")
        self.formLayout_3.setWidget(1, QtGui.QFormLayout.FieldRole, self.ampawindowstepSpinBox)
        self.ampanoisethresholdLabel = QtGui.QLabel(self.ampaGeneralSettingsGroupBox)
        self.ampanoisethresholdLabel.setObjectName("ampanoisethresholdLabel")
        self.formLayout_3.setWidget(2, QtGui.QFormLayout.LabelRole, self.ampanoisethresholdLabel)
        self.ampanoisethresholdSpinBox = QtGui.QSpinBox(self.ampaGeneralSettingsGroupBox)
        self.ampanoisethresholdSpinBox.setAccelerated(True)
        self.ampanoisethresholdSpinBox.setMinimum(1)
        self.ampanoisethresholdSpinBox.setProperty("value", 90)
        self.ampanoisethresholdSpinBox.setObjectName("ampanoisethresholdSpinBox")
        self.formLayout_3.setWidget(2, QtGui.QFormLayout.FieldRole, self.ampanoisethresholdSpinBox)
        self.horizontalLayout.addWidget(self.ampaGeneralSettingsGroupBox)

        # Set AMPA filter bank settings Group Box
        self.filterbankGroupBox = QtGui.QGroupBox(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.filterbankGroupBox.sizePolicy().hasHeightForWidth())
        self.filterbankGroupBox.setSizePolicy(sizePolicy)
        self.filterbankGroupBox.setObjectName("filterbankGroupBox")
        self.filterbankGroupBox.setVisible(False)
        self.formLayout_2 = QtGui.QFormLayout(self.filterbankGroupBox)
        self.formLayout_2.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout_2.setContentsMargins(24, 24, 24, 24)
        self.formLayout_2.setVerticalSpacing(24)
        self.formLayout_2.setObjectName("formLayout_2")
        self.startfLabel = QtGui.QLabel(self.filterbankGroupBox)
        self.startfLabel.setObjectName("startfLabel")
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.startfLabel)
        self.startfSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.startfSpinBox.setAccelerated(True)
        self.startfSpinBox.setMaximum(100.0)
        self.startfSpinBox.setSingleStep(0.01)
        self.startfSpinBox.setProperty("value", 2.0)
        self.startfSpinBox.setObjectName("startfSpinBox")
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.startfSpinBox)
        self.endfLabel = QtGui.QLabel(self.filterbankGroupBox)
        self.endfLabel.setObjectName("endfLabel")
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.endfLabel)
        self.endfSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.endfSpinBox.setAccelerated(True)
        self.endfSpinBox.setMaximum(100.0)
        self.endfSpinBox.setSingleStep(0.01)
        self.endfSpinBox.setProperty("value", 12.0)
        self.endfSpinBox.setObjectName("endfSpinBox")
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.endfSpinBox)
        self.bandwidthLabel = QtGui.QLabel(self.filterbankGroupBox)
        self.bandwidthLabel.setObjectName("bandwidthLabel")
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.LabelRole, self.bandwidthLabel)
        self.bandwidthSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.bandwidthSpinBox.setAccelerated(True)
        self.bandwidthSpinBox.setMinimum(1.0)
        self.bandwidthSpinBox.setMaximum(100.0)
        self.bandwidthSpinBox.setSingleStep(0.01)
        self.bandwidthSpinBox.setProperty("value", 3.0)
        self.bandwidthSpinBox.setObjectName("bandwidthSpinBox")
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.FieldRole, self.bandwidthSpinBox)
        self.overlapLabel = QtGui.QLabel(self.filterbankGroupBox)
        self.overlapLabel.setObjectName("overlapLabel")
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.LabelRole, self.overlapLabel)
        self.overlapSpinBox = QtGui.QDoubleSpinBox(self.filterbankGroupBox)
        self.overlapSpinBox.setAccelerated(True)
        self.overlapSpinBox.setMinimum(0.0)
        self.overlapSpinBox.setMaximum(100.0)
        self.overlapSpinBox.setSingleStep(0.01)
        self.overlapSpinBox.setProperty("value", 1.0)
        self.overlapSpinBox.setObjectName("overlapSpinBox")
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.FieldRole, self.overlapSpinBox)

        # Set AMPA filters Group Box
        self.horizontalLayout.addWidget(self.filterbankGroupBox)
        self.ampaFiltersGroupBox = QtGui.QGroupBox(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.ampaFiltersGroupBox.sizePolicy().hasHeightForWidth())
        self.ampaFiltersGroupBox.setSizePolicy(sizePolicy)
        self.ampaFiltersGroupBox.setObjectName("ampaFiltersGroupBox")
        self.ampaFiltersGroupBox.setVisible(False)
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.ampaFiltersGroupBox)
        self.verticalLayout_2.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.ampafiltersToolBar = QtGui.QToolBar(self.ampaFiltersGroupBox)
        self.ampafiltersToolBar.setMovable(False)
        self.actionAddFilter = QtGui.QAction(self)
        self.actionAddFilter.setIcon(QtGui.QIcon.fromTheme("list-add"))
        self.actionRemoveFilter = QtGui.QAction(self)
        self.actionRemoveFilter.setIcon(QtGui.QIcon.fromTheme("list-remove"))
        self.actionRemoveFilter.setEnabled(False)
        self.ampafiltersToolBar.addAction(self.actionAddFilter)
        self.ampafiltersToolBar.addAction(self.actionRemoveFilter)

        self.filtersTable = QtGui.QTableView(self.ampaFiltersGroupBox)
        self.filtersTable.setCornerButtonEnabled(True)
        self.filtersTable.setObjectName("filtersTable")
        self.filtersTable.horizontalHeader().setStretchLastSection(True)
        self.filtersTable.verticalHeader().setVisible(False)
        self.filtersTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.filtersTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.filtersTable.setShowGrid(False)
        self.verticalLayout_2.addWidget(self.ampafiltersToolBar)
        self.verticalLayout_2.addWidget(self.filtersTable)
        self.horizontalLayout.addWidget(self.ampaFiltersGroupBox)

        # Set Takanami Group Box
        self.takanamiGroupBox = QtGui.QGroupBox(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.takanamiGroupBox.sizePolicy().hasHeightForWidth())
        self.takanamiGroupBox.setSizePolicy(sizePolicy)
        self.takanamiGroupBox.setObjectName("takanamiGroupBox")
        self.takanamiGroupBox.setVisible(False)
        self.takanamiformLayout = QtGui.QFormLayout(self.takanamiGroupBox)
        self.takanamiformLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.takanamiformLayout.setContentsMargins(24, 24, 24, 24)
        self.takanamiformLayout.setVerticalSpacing(24)
        self.takanamiformLayout.setObjectName("takanamiformLayout")
        self.takanamiCheckBox = QtGui.QCheckBox(self.takanamiGroupBox)
        self.takanamiCheckBox.setObjectName("takanamiCheckBox")
        self.takanamiCheckBox.setChecked(True)
        self.takanamiformLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.takanamiCheckBox)
        self.takanamiMarginLabel = QtGui.QLabel(self.takanamiGroupBox)
        self.takanamiformLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.takanamiMarginLabel)
        self.takanamiMarginSpinBox = QtGui.QDoubleSpinBox(self.takanamiGroupBox)
        self.takanamiMarginSpinBox.setAccelerated(True)
        self.takanamiMarginSpinBox.setMinimum(1.0)
        self.takanamiMarginSpinBox.setMaximum(20.0)
        self.takanamiMarginSpinBox.setSingleStep(0.01)
        self.takanamiformLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.takanamiMarginSpinBox)
        self.horizontalLayout.addWidget(self.takanamiGroupBox)

        # Set Player Group Box
        self.playerGroupBox = QtGui.QGroupBox(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.playerGroupBox.sizePolicy().hasHeightForWidth())
        self.playerGroupBox.setSizePolicy(sizePolicy)
        self.playerGroupBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.playerGroupBox.setVisible(False)
        self.formLayout = QtGui.QFormLayout(self.playerGroupBox)
        self.formLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setRowWrapPolicy(QtGui.QFormLayout.DontWrapRows)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.formLayout.setContentsMargins(24, 24, 24, 24)
        self.formLayout.setHorizontalSpacing(9)
        self.formLayout.setVerticalSpacing(24)
        self.samplerateLabel = QtGui.QLabel(self.playerGroupBox)
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.samplerateLabel)
        self.samplerateComboBox = QtGui.QComboBox(self.playerGroupBox)
        self.samplerateComboBox.addItems([str(item) for item in playertoolbar.sample_rates])
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.samplerateComboBox)
        self.bitdepthLabel = QtGui.QLabel(self.playerGroupBox)
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.bitdepthLabel)
        self.bitdepthComboBox = QtGui.QComboBox(self.playerGroupBox)
        self.bitdepthComboBox.addItems([str(item) for item in playertoolbar.bit_depths])
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.bitdepthComboBox)
        self.horizontalLayout.addWidget(self.playerGroupBox)

        # Button Box
        self.verticalLayout.addWidget(self.widget)
        self.buttonBox = QtGui.QDialogButtonBox(SettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SettingsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

        self._settingsMenus = {}
        self._settingsMenus[self.treeWidget.topLevelItem(0).text(0)] = self.staltaGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(1).child(0).text(0)] = self.ampaGeneralSettingsGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(1).child(1).text(0)] = self.ampaFiltersGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(1).child(1).text(0)] = self.ampaFiltersGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(1).child(2).text(0)] = self.filterbankGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(2).text(0)] = self.takanamiGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(3).text(0)] = self.playerGroupBox
        self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(0))
        self.currentMenu = self.staltaGroupBox

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(QtGui.QApplication.translate("SettingsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0, QtGui.QApplication.translate("SettingsDialog", "1", None, QtGui.QApplication.UnicodeUTF8))
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.topLevelItem(0).setText(0, QtGui.QApplication.translate("SettingsDialog", "STA-LTA", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).setText(0, QtGui.QApplication.translate("SettingsDialog", "AMPA", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).child(0).setText(0, QtGui.QApplication.translate("SettingsDialog", "General Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).child(1).setText(0, QtGui.QApplication.translate("SettingsDialog", "Filters", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).child(2).setText(0, QtGui.QApplication.translate("SettingsDialog", "Filter Bank Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(2).setText(0, QtGui.QApplication.translate("SettingsDialog", "Takanami", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(3).setText(0, QtGui.QApplication.translate("SettingsDialog", "Player", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.setSortingEnabled(__sortingEnabled)
        self.staltaGroupBox.setTitle(QtGui.QApplication.translate("SettingsDialog", "STA-LTA Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.staLabel.setText(QtGui.QApplication.translate("SettingsDialog", "STA window (in seconds):", None, QtGui.QApplication.UnicodeUTF8))
        self.ltaLabel.setText(QtGui.QApplication.translate("SettingsDialog", "LTA window (in seconds):", None, QtGui.QApplication.UnicodeUTF8))
        self.takanamiGroupBox.setTitle(QtGui.QApplication.translate("SettingsDialog", "Takanami Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.takanamiCheckBox.setText(QtGui.QApplication.translate("SettingsDialog", "Apply Takanami on results", None, QtGui.QApplication.UnicodeUTF8))
        self.takanamiMarginLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Takanami Max. Margin (in seconds):", None, QtGui.QApplication.UnicodeUTF8))
        self.ampaGeneralSettingsGroupBox.setTitle(QtGui.QApplication.translate("SettingsDialog", "AMPA General Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.ampawindowLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Sliding Window Length (in seconds):", None, QtGui.QApplication.UnicodeUTF8))
        self.ampawindowstepLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Sliding Window Step (in seconds):", None, QtGui.QApplication.UnicodeUTF8))
        self.ampanoisethresholdLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Noise Threshold Percentile:", None, QtGui.QApplication.UnicodeUTF8))
        self.filterbankGroupBox.setTitle(QtGui.QApplication.translate("SettingsDialog", "AMPA Filter Bank Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.startfLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Start Frequency (Hz):", None, QtGui.QApplication.UnicodeUTF8))
        self.endfLabel.setText(QtGui.QApplication.translate("SettingsDialog", "End Frequency (Hz):", None, QtGui.QApplication.UnicodeUTF8))
        self.bandwidthLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Channel Bandwidth (Hz):", None, QtGui.QApplication.UnicodeUTF8))
        self.overlapLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Channel Overlap (Hz):", None, QtGui.QApplication.UnicodeUTF8))
        self.ampaFiltersGroupBox.setTitle(QtGui.QApplication.translate("SettingsDialog", "AMPA Filters", None, QtGui.QApplication.UnicodeUTF8))
        self.filtersTable.setSortingEnabled(True)
        self.playerGroupBox.setTitle(QtGui.QApplication.translate("SettingsDialog", "Player Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.samplerateLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Sample rate (samples/sec.):", None, QtGui.QApplication.UnicodeUTF8))
        self.bitdepthLabel.setText(QtGui.QApplication.translate("SettingsDialog", "Bit Depth:", None, QtGui.QApplication.UnicodeUTF8))

