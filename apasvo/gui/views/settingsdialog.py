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

from PySide import QtGui
from PySide import QtCore

from apasvo.gui.views import playertoolbar
from apasvo.picking import record as rc
from apasvo.utils import plotting

from apasvo._version import _application_name
from apasvo._version import _organization


COLOR_KEYS = ("method", "mode", "status")
COLOR_KEYS_LABELS = ("Picking method", "Picking mode", "Status")
DEFAULT_COLOR_KEY = "method"
DEFAULT_STALTA_COLOR = "#ffa500"
DEFAULT_STALTA_TAKANAMI_COLOR = "#ffa500"
DEFAULT_AMPA_COLOR = "#adff2f"
DEFAULT_AMPA_TAKANAMI_COLOR = "#adff2f"
DEFAULT_TAKANAMI_COLOR = "#dda0dd"
DEFAULT_OTHER_COLOR = "#d3d3d3"
DEFAULT_MANUAL_COLOR = "#f08080"
DEFAULT_AUTOMATIC_COLOR = "#87ceeb"
DEFAULT_REPORTED_COLOR = "#ffa500"
DEFAULT_REVISED_COLOR = "#87ceeb"
DEFAULT_CONFIRMED_COLOR = "#adff2f"
DEFAULT_REJECTED_COLOR = "#f08080"
DEFAULT_UNDEFINED_COLOR = "#d3d3d3"
SPECGRAM_WINDOW_LENGTHS = (16, 32, 64, 128, 256, 512, 1024, 2048)

DEFAULT_COLOR_SCHEME = ((rc.method_stalta, DEFAULT_STALTA_COLOR),
                        (rc.method_stalta_takanami, DEFAULT_STALTA_TAKANAMI_COLOR),
                        (rc.method_ampa, DEFAULT_AMPA_COLOR),
                        (rc.method_ampa_takanami, DEFAULT_AMPA_TAKANAMI_COLOR),
                        (rc.method_takanami, DEFAULT_TAKANAMI_COLOR),
                        (rc.method_other, DEFAULT_OTHER_COLOR))


class SettingsDialog(QtGui.QDialog):
    """A dialog window to edit application settings.
    """

    saved = QtCore.Signal()

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setup_ui()

        self.colorKeyComboBox.currentIndexChanged.connect(self._keyChanged)
        self.colorMethodOtherButton.clicked.connect(self._colorButtonClicked)
        self.colorMethodTakanamiButton.clicked.connect(self._colorButtonClicked)
        self.colorMethodStaLtaButton.clicked.connect(self._colorButtonClicked)
        self.colorMethodStaLtaTakanamiButton.clicked.connect(self._colorButtonClicked)
        self.colorMethodAmpaButton.clicked.connect(self._colorButtonClicked)
        self.colorMethodAmpaTakanamiButton.clicked.connect(self._colorButtonClicked)
        self.colorModeManualButton.clicked.connect(self._colorButtonClicked)
        self.colorModeAutomaticButton.clicked.connect(self._colorButtonClicked)
        self.colorStatusReportedButton.clicked.connect(self._colorButtonClicked)
        self.colorStatusRevisedButton.clicked.connect(self._colorButtonClicked)
        self.colorStatusConfirmedButton.clicked.connect(self._colorButtonClicked)
        self.colorStatusRejectedButton.clicked.connect(self._colorButtonClicked)
        self.colorStatusUndefinedButton.clicked.connect(self._colorButtonClicked)

        self.windowlenComboBox.currentIndexChanged.connect(lambda i: self.noverlapSpinBox.setMaximum(SPECGRAM_WINDOW_LENGTHS[i] - 1))

        self.treeWidget.currentItemChanged.connect(self._itemChanged)
        self.buttonBox.clicked.connect(self.onclick)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.loadSettings()

    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumHeight(480)
        self.setMinimumWidth(640)

        # Set the settings tree widget
        self.treeWidget = QtGui.QTreeWidget(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum,
                                       QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().
                                     hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setMaximumWidth(180)
        self.treeWidget.setAnimated(False)
        self.treeWidget.setHeaderHidden(True)

        # Set Player Group Box
        self.playerGroupBox = QtGui.QGroupBox("Audio Player", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.playerGroupBox.sizePolicy().
                                     hasHeightForWidth())
        self.playerGroupBox.setSizePolicy(sizePolicy)
        self.playerGroupBox.setAlignment(QtCore.Qt.AlignLeading |
                                         QtCore.Qt.AlignLeft |
                                         QtCore.Qt.AlignVCenter)
        self.playerGroupBox.setVisible(True)
        self.formLayout = QtGui.QFormLayout(self.playerGroupBox)
        self.formLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setRowWrapPolicy(QtGui.QFormLayout.DontWrapRows)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight |
                                          QtCore.Qt.AlignTrailing |
                                          QtCore.Qt.AlignVCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignLeading |
                                         QtCore.Qt.AlignLeft |
                                         QtCore.Qt.AlignTop)
        self.formLayout.setContentsMargins(24, 24, 24, 24)
        self.formLayout.setHorizontalSpacing(24)
        self.formLayout.setVerticalSpacing(24)
        self.playbackfreqLabel = QtGui.QLabel("Playback frequency (Hz):",
                                            self.playerGroupBox)
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole,
                                  self.playbackfreqLabel)
        self.playbackrateSpinBox = QtGui.QSpinBox(self.playerGroupBox)
        self.playbackrateSpinBox.setMinimum(100)
        self.playbackrateSpinBox.setMaximum(16000)
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole,
                                  self.playbackrateSpinBox)
        self.bitdepthLabel = QtGui.QLabel("Sample Format:", self.playerGroupBox)
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole,
                                  self.bitdepthLabel)
        self.bitdepthComboBox = QtGui.QComboBox(self.playerGroupBox)
        self.bitdepthComboBox.addItems(playertoolbar.bit_depths.keys())
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole,
                                  self.bitdepthComboBox)

        # set colors group box
        self.colorsGroupBox = QtGui.QGroupBox("Colors", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.colorsGroupBox.sizePolicy().
                                     hasHeightForWidth())
        self.colorsGroupBox.setSizePolicy(sizePolicy)
        self.colorsGroupBox.setAlignment(QtCore.Qt.AlignLeading |
                                         QtCore.Qt.AlignLeft |
                                         QtCore.Qt.AlignVCenter)
        self.colorsGroupBox.setVisible(False)
        self.colorsLayout = QtGui.QVBoxLayout(self.colorsGroupBox)

        self.colorKeyWidget = QtGui.QWidget(self.colorsGroupBox)
        self.colorKeyLayout = QtGui.QFormLayout(self.colorKeyWidget)
        self.colorKeyLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.colorKeyLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.colorKeyLayout.setRowWrapPolicy(QtGui.QFormLayout.DontWrapRows)
        self.colorKeyLayout.setLabelAlignment(QtCore.Qt.AlignRight |
                                          QtCore.Qt.AlignTrailing |
                                          QtCore.Qt.AlignVCenter)
        self.colorKeyLayout.setFormAlignment(QtCore.Qt.AlignLeading |
                                         QtCore.Qt.AlignLeft |
                                         QtCore.Qt.AlignTop)
        self.colorKeyLayout.setContentsMargins(24, 24, 24, 24)
        self.colorKeyLayout.setHorizontalSpacing(24)
        self.colorKeyLabel = QtGui.QLabel("Key to color the events:", self.colorsGroupBox)
        self.colorKeyComboBox = QtGui.QComboBox(self.colorsGroupBox)
        self.colorKeyComboBox.addItems(COLOR_KEYS_LABELS)
        self.colorKeyLayout.setWidget(0, QtGui.QFormLayout.LabelRole,
                                  self.colorKeyLabel)
        self.colorKeyLayout.setWidget(0, QtGui.QFormLayout.FieldRole,
                                  self.colorKeyComboBox)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Expanding)
        # color by method buttons
        self.colorMethodButtonsWidget = QtGui.QWidget(self.colorsGroupBox)
        self.colorMethodButtonsWidget.setSizePolicy(sizePolicy)
        self.colorMethodButtonsLayout = QtGui.QVBoxLayout(self.colorMethodButtonsWidget)
        self.colorMethodButtonsLayout.setAlignment(QtCore.Qt.AlignTop)
        self.colorMethodTakanamiButton = QtGui.QPushButton("Takanami method", self.colorMethodButtonsWidget)
        self.colorMethodStaLtaButton = QtGui.QPushButton("STA-LTA method", self.colorMethodButtonsWidget)
        self.colorMethodStaLtaTakanamiButton = QtGui.QPushButton("STA-LTA + Takanami method", self.colorMethodButtonsWidget)
        self.colorMethodAmpaButton = QtGui.QPushButton("AMPA method", self.colorMethodButtonsWidget)
        self.colorMethodAmpaTakanamiButton = QtGui.QPushButton("AMPA + Takanami method", self.colorMethodButtonsWidget)
        self.colorMethodOtherButton = QtGui.QPushButton("Other method", self.colorMethodButtonsWidget)
        self.colorMethodButtonsLayout.addWidget(self.colorMethodStaLtaButton)
        self.colorMethodButtonsLayout.addWidget(self.colorMethodStaLtaTakanamiButton)
        self.colorMethodButtonsLayout.addWidget(self.colorMethodAmpaButton)
        self.colorMethodButtonsLayout.addWidget(self.colorMethodAmpaTakanamiButton)
        self.colorMethodButtonsLayout.addWidget(self.colorMethodTakanamiButton)
        self.colorMethodButtonsLayout.addWidget(self.colorMethodOtherButton)
        self.colorMethodButtonsWidget.setVisible(False)

        # color by mode buttons
        self.colorModeButtonsWidget = QtGui.QWidget(self.colorsGroupBox)
        self.colorModeButtonsWidget.setSizePolicy(sizePolicy)
        self.colorModeButtonsLayout = QtGui.QVBoxLayout(self.colorModeButtonsWidget)
        self.colorModeButtonsLayout.setAlignment(QtCore.Qt.AlignTop)
        self.colorModeManualButton = QtGui.QPushButton("Manual", self.colorModeButtonsWidget)
        self.colorModeAutomaticButton = QtGui.QPushButton("Automatic", self.colorModeButtonsWidget)
        self.colorModeButtonsLayout.addWidget(self.colorModeManualButton)
        self.colorModeButtonsLayout.addWidget(self.colorModeAutomaticButton)
        self.colorModeButtonsWidget.setVisible(False)

        # color by status buttons
        self.colorStatusButtonsWidget = QtGui.QWidget(self.colorsGroupBox)
        self.colorStatusButtonsWidget.setSizePolicy(sizePolicy)
        self.colorStatusButtonsLayout = QtGui.QVBoxLayout(self.colorStatusButtonsWidget)
        self.colorStatusButtonsLayout.setAlignment(QtCore.Qt.AlignTop)
        self.colorStatusReportedButton = QtGui.QPushButton("Reported", self.colorStatusButtonsWidget)
        self.colorStatusRevisedButton = QtGui.QPushButton("Revised", self.colorStatusButtonsWidget)
        self.colorStatusConfirmedButton = QtGui.QPushButton("Confirmed", self.colorStatusButtonsWidget)
        self.colorStatusRejectedButton = QtGui.QPushButton("Rejected", self.colorStatusButtonsWidget)
        self.colorStatusUndefinedButton = QtGui.QPushButton("Undefined", self.colorStatusButtonsWidget)
        self.colorStatusButtonsLayout.addWidget(self.colorStatusReportedButton)
        self.colorStatusButtonsLayout.addWidget(self.colorStatusRevisedButton)
        self.colorStatusButtonsLayout.addWidget(self.colorStatusConfirmedButton)
        self.colorStatusButtonsLayout.addWidget(self.colorStatusRejectedButton)
        self.colorStatusButtonsLayout.addWidget(self.colorStatusUndefinedButton)
        self.colorStatusButtonsWidget.setVisible(False)

        self.colorsLayout.addWidget(self.colorKeyWidget)
        self.colorsLayout.addWidget(self.colorMethodButtonsWidget)
        self.colorsLayout.addWidget(self.colorModeButtonsWidget)
        self.colorsLayout.addWidget(self.colorStatusButtonsWidget)

        # Set Spectrogram Group Box
        self.specgramGroupBox = QtGui.QGroupBox("Spectrogram", self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.specgramGroupBox.sizePolicy().
                                     hasHeightForWidth())
        self.specgramGroupBox.setSizePolicy(sizePolicy)
        self.specgramGroupBox.setAlignment(QtCore.Qt.AlignLeading |
                                         QtCore.Qt.AlignLeft |
                                         QtCore.Qt.AlignVCenter)
        self.specgramGroupBox.setVisible(False)
        self.specgramFormLayout = QtGui.QFormLayout(self.specgramGroupBox)
        self.specgramFormLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.specgramFormLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.specgramFormLayout.setRowWrapPolicy(QtGui.QFormLayout.DontWrapRows)
        self.specgramFormLayout.setLabelAlignment(QtCore.Qt.AlignRight |
                                          QtCore.Qt.AlignTrailing |
                                          QtCore.Qt.AlignVCenter)
        self.specgramFormLayout.setFormAlignment(QtCore.Qt.AlignLeading |
                                         QtCore.Qt.AlignLeft |
                                         QtCore.Qt.AlignTop)
        self.specgramFormLayout.setContentsMargins(24, 24, 24, 24)
        self.specgramFormLayout.setHorizontalSpacing(24)
        self.specgramFormLayout.setVerticalSpacing(24)
        self.windowlenLabel = QtGui.QLabel("Window length (in samples):",
                                           self.specgramGroupBox)
        self.windowlenComboBox = QtGui.QComboBox(self.specgramGroupBox)
        self.windowlenComboBox.addItems(map(str, SPECGRAM_WINDOW_LENGTHS))
        self.noverlapLabel = QtGui.QLabel("Overlap (in samples):",
                                             self.specgramGroupBox)
        self.noverlapSpinBox = QtGui.QSpinBox(self.specgramGroupBox)
        self.noverlapSpinBox.setMinimum(0)
        self.windowLabel = QtGui.QLabel("Window type:", self.specgramGroupBox)
        self.windowComboBox = QtGui.QComboBox(self.specgramGroupBox)
        self.windowComboBox.addItems(plotting.SPECGRAM_WINDOWS_NAMES)
        self.specgramFormLayout.setWidget(0, QtGui.QFormLayout.LabelRole,
                                          self.windowlenLabel)
        self.specgramFormLayout.setWidget(0, QtGui.QFormLayout.FieldRole,
                                          self.windowlenComboBox)
        self.specgramFormLayout.setWidget(1, QtGui.QFormLayout.LabelRole,
                                          self.noverlapLabel)
        self.specgramFormLayout.setWidget(1, QtGui.QFormLayout.FieldRole,
                                          self.noverlapSpinBox)
        self.specgramFormLayout.setWidget(2, QtGui.QFormLayout.LabelRole,
                                          self.windowLabel)
        self.specgramFormLayout.setWidget(2, QtGui.QFormLayout.FieldRole,
                                          self.windowComboBox)

        # Button Box
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply |
                                          QtGui.QDialogButtonBox.Cancel |
                                          QtGui.QDialogButtonBox.Ok)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)

        # Set layouts
        self.settings_frame = QtGui.QFrame(self)
        self.horizontalLayout = QtGui.QHBoxLayout(self.settings_frame)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.addWidget(self.treeWidget)
        self.horizontalLayout.addWidget(self.playerGroupBox)
        self.horizontalLayout.addWidget(self.colorsGroupBox)
        self.horizontalLayout.addWidget(self.specgramGroupBox)

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.settings_frame)
        self.verticalLayout.addWidget(self.buttonBox)
        self.setLayout(self.verticalLayout)

        self.item_player = QtGui.QTreeWidgetItem(self.treeWidget)
        self.item_colors = QtGui.QTreeWidgetItem(self.treeWidget)
        self.item_specgram = QtGui.QTreeWidgetItem(self.treeWidget)
        self.item_player.setText(0, self.playerGroupBox.title())
        self.item_colors.setText(0, self.colorsGroupBox.title())
        self.item_specgram.setText(0, self.specgramGroupBox.title())

        self.treeWidget.addTopLevelItem(self.item_player)
        self.treeWidget.setSortingEnabled(False)

        self._settingsMenus = {}
        self._settingsMenus[self.treeWidget.topLevelItem(0).text(0)] = self.playerGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(1).text(0)] = self.colorsGroupBox
        self._settingsMenus[self.treeWidget.topLevelItem(2).text(0)] = self.specgramGroupBox
        self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(0))
        self.currentMenu = self.playerGroupBox

    def loadSettings(self):
        """Loads settings from persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)

        settings.beginGroup("player_settings")
        self.playbackrateSpinBox.setValue(int(settings.value('playback_freq', playertoolbar.DEFAULT_REAL_FREQ)))
        bit_depth_index = playertoolbar.bit_depths.values().index(settings.value('bit_depth', playertoolbar.DEFAULT_BIT_DEPTH))
        self.bitdepthComboBox.setCurrentIndex(bit_depth_index)
        settings.endGroup()

        settings.beginGroup("color_settings")
        key = int(settings.value('color_key', COLOR_KEYS.index(DEFAULT_COLOR_KEY)))
        self.colorKeyComboBox.setCurrentIndex(key)
        self._keyChanged(key)
        mColor = QtGui.QColor(settings.value(rc.method_stalta, DEFAULT_STALTA_COLOR))
        self.colorMethodStaLtaButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.method_stalta_takanami, DEFAULT_STALTA_TAKANAMI_COLOR))
        self.colorMethodStaLtaTakanamiButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.method_ampa, DEFAULT_AMPA_COLOR))
        self.colorMethodAmpaButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.method_ampa_takanami, DEFAULT_AMPA_TAKANAMI_COLOR))
        self.colorMethodAmpaTakanamiButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.method_takanami, DEFAULT_TAKANAMI_COLOR))
        self.colorMethodTakanamiButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.method_other, DEFAULT_OTHER_COLOR))
        self.colorMethodOtherButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.mode_manual, DEFAULT_MANUAL_COLOR))
        self.colorModeManualButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.mode_automatic, DEFAULT_AUTOMATIC_COLOR))
        self.colorModeAutomaticButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.status_reported, DEFAULT_REPORTED_COLOR))
        self.colorStatusReportedButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.status_revised, DEFAULT_REVISED_COLOR))
        self.colorStatusRevisedButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.status_confirmed, DEFAULT_CONFIRMED_COLOR))
        self.colorStatusConfirmedButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.status_rejected, DEFAULT_REJECTED_COLOR))
        self.colorStatusRejectedButton.setStyleSheet("background-color: %s" % mColor.name())
        mColor = QtGui.QColor(settings.value(rc.status_undefined, DEFAULT_UNDEFINED_COLOR))
        self.colorStatusUndefinedButton.setStyleSheet("background-color: %s" % mColor.name())
        settings.endGroup()

        settings.beginGroup("specgram_settings")
        windowlen = int(settings.value('window_len', SPECGRAM_WINDOW_LENGTHS[4]))
        self.windowlenComboBox.setCurrentIndex(SPECGRAM_WINDOW_LENGTHS.index(windowlen))
        self.noverlapSpinBox.setMaximum(windowlen - 1)
        self.noverlapSpinBox.setValue(int(settings.value('noverlap', windowlen / 2)))
        mwindow = settings.value('window', plotting.SPECGRAM_WINDOWS[2])
        self.windowComboBox.setCurrentIndex(plotting.SPECGRAM_WINDOWS.index(mwindow))
        settings.endGroup()

    def saveSettings(self):
        """Saves settings to persistent storage."""
        settings = QtCore.QSettings(_organization, _application_name)

        settings.beginGroup("player_settings")
        settings.setValue('playback_freq', self.playbackrateSpinBox.value())
        settings.setValue('bit_depth',
                          playertoolbar.bit_depths[self.bitdepthComboBox.currentText()])
        settings.endGroup()

        settings.beginGroup("color_settings")
        settings.setValue('color_key', self.colorKeyComboBox.currentIndex())
        settings.setValue(rc.method_stalta, self.colorMethodStaLtaButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.method_stalta_takanami, self.colorMethodStaLtaTakanamiButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.method_ampa, self.colorMethodAmpaButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.method_ampa_takanami, self.colorMethodAmpaTakanamiButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.method_takanami, self.colorMethodTakanamiButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.method_other, self.colorMethodOtherButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.mode_manual, self.colorModeManualButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.mode_automatic, self.colorModeAutomaticButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.status_reported, self.colorStatusReportedButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.status_revised, self.colorStatusRevisedButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.status_confirmed, self.colorStatusConfirmedButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.status_rejected, self.colorStatusRejectedButton.palette().color(QtGui.QPalette.Background))
        settings.setValue(rc.status_undefined, self.colorStatusUndefinedButton.palette().color(QtGui.QPalette.Background))
        settings.endGroup()

        settings.beginGroup("specgram_settings")
        settings.setValue('window_len', SPECGRAM_WINDOW_LENGTHS[self.windowlenComboBox.currentIndex()])
        settings.setValue('noverlap', self.noverlapSpinBox.value())
        settings.setValue('window', plotting.SPECGRAM_WINDOWS[self.windowComboBox.currentIndex()])
        settings.endGroup()

        self.saved.emit()

    def onclick(self, button):
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Apply:
            self.saveSettings()
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Ok:
            self.saveSettings()

    def _itemChanged(self, current, previous):
        item_name = current.text(0)
        if item_name in self._settingsMenus:
            if self.currentMenu != self._settingsMenus[item_name]:
                self.currentMenu.setVisible(False)
                self._settingsMenus[item_name].setVisible(True)
                self.currentMenu = self._settingsMenus[item_name]

    def _keyChanged(self, index):
        if index == 0:
            self.colorMethodButtonsWidget.setVisible(True)
            self.colorModeButtonsWidget.setVisible(False)
            self.colorStatusButtonsWidget.setVisible(False)
        elif index == 1:
            self.colorMethodButtonsWidget.setVisible(False)
            self.colorModeButtonsWidget.setVisible(True)
            self.colorStatusButtonsWidget.setVisible(False)
        elif index == 2:
            self.colorMethodButtonsWidget.setVisible(False)
            self.colorModeButtonsWidget.setVisible(False)
            self.colorStatusButtonsWidget.setVisible(True)

    def _colorButtonClicked(self):
        button = self.sender()
        mBackgroundColor = button.palette().color(QtGui.QPalette.Background)
        mColor = QtGui.QColorDialog.getColor(mBackgroundColor)
        button.setStyleSheet("background-color: %s" % mColor.name())
