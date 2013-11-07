#!/usr/bin/python2.7
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

import sys
from PySide import QtGui, QtCore

from gui.views.converted import ui_mainwindow
from gui.delegates import cbdelegate
from gui.models import eventlistmodel
from gui.views import svwidget
from gui.views import loaddialog
from gui.views import settingsdialog
from gui.views import pickingtaskdialog

from picking import stalta
from picking import ampa
from picking import record as rc

from _version import __version__
from _version import _application_name
from _version import _organization


class MainWindow(QtGui.QMainWindow, ui_mainwindow.Ui_MainWindow):
    """Application Main Window class. SDI GUI style.

    Attributes:
        record: Current opened seismic document.
        isModified: Indicates whether there are any changes in results to save
            or not.
        saved_filename: Name of the file where results are being saved.
    """

    windowList = []    # A list of opened application windows
    MaxRecentFiles = 10    # Recent files list max size

    def __init__(self, parent=None, filename=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.record = None
        self._model = None
        self.isModified = False
        self.saved_filename = None

        stateDelegate = cbdelegate.ComboBoxDelegate(self.EventsTableView, rc.Event.statuses)
        self.EventsTableView.setItemDelegateForColumn(5, stateDelegate)
        self.EventsTableView.clicked.connect(self.goToEventPosition)

        self.actionOpen.triggered.connect(self.open)
        self.actionSave.triggered.connect(self.save)
        self.actionSave_As.triggered.connect(self.save_as)
        self.actionClose.triggered.connect(self.close)
        self.actionQuit.triggered.connect(QtGui.qApp.closeAllWindows)
        self.actionClearRecent.triggered.connect(self.clear_recent_list)
        self.actionSettings.triggered.connect(self.edit_settings)
        self.actionSTA_LTA.triggered.connect(self.doSTALTA)
        self.actionAMPA.triggered.connect(self.doAMPA)

        self.signalViewer = svwidget.SignalViewerWidget(self.splitter)
        self.splitter.addWidget(self.signalViewer)
        self.toolBarNavigation = svwidget.NavigationToolbar(self.signalViewer.canvas,
                                                   self)
        self.toolBarNavigation.setEnabled(False)
        self.toolBarMain.setObjectName("toolBarNavigation")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarNavigation)
        self.addToolBarBreak()
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarAnalysis)

        self.actionEvent_List.toggled.connect(self.EventsTableView.setVisible)
        self.actionSignal_Amplitude.toggled.connect(self.signalViewer.set_signal_amplitude_visible)
        self.actionSignal_Envelope.toggled.connect(self.signalViewer.set_signal_envelope_visible)
        self.actionEspectrogram.toggled.connect(self.signalViewer.set_espectrogram_visible)
        self.actionCharacteristic_Function.toggled.connect(self.signalViewer.set_cf_visible)
        self.actionSignal_MiniMap.toggled.connect(self.signalViewer.set_minimap_visible)
        self.signalViewer.selector.toogled.connect(self.actionTakanami.setEnabled)
        self.thresholdCheckBox.toggled.connect(self.toogle_threshold)
        self.actionMain_Toolbar.toggled.connect(self.toolBarMain.setVisible)
        self.actionMedia_Toolbar.toggled.connect(self.toolBarMedia.setVisible)
        self.actionAnalysis_Toolbar.toggled.connect(self.toolBarAnalysis.setVisible)
        self.actionNavigation_Toolbar.toggled.connect(self.toolBarNavigation.setVisible)

        if filename is not None:
            self.open(filename)

        self.set_title()
        self.set_recent_menu()

    def open(self, filename=None):
        """Opens a new document.

        Opens selected document in the current window if it isn't currently
        showing a document, otherwise the document is opened in a new
        window.

        Args:
            filename: Selected document. If None is provided launches a
            file dialog to let the user select a file.
            Default: None.
        """
        if filename is None:
            filename, _ = QtGui.QFileDialog.getOpenFileName(self, "Open Data File", ".",
                                                            "Binary Files (*.bin *.raw);;Text Files (*.txt);;All Files (*.*)")
        if filename != '':
            if self.record is None:
                dialog = loaddialog.LoadDialog(self, filename)
                return_code = dialog.exec_()
                if return_code == QtGui.QDialog.Accepted:
                    values = dialog.get_values()
                    # Load and visualize the opened record
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                    self.record = rc.Record(filename, **values)
                    self._model = eventlistmodel.EventListModel(self.record, ['name', 'time',
                                                               'cf_value',
                                                               'mode',
                                                               'method',
                                                               'status',
                                                               'comments'])
                    self._model.emptyList.connect(self.set_modified)
                    ########
                    self.EventsTableView.setModel(self._model)
                    self.signalViewer.set_record(self.record)
                    self.signalViewer.thresholdMarker.thresholdChanged.connect(self.thresholdSpinBox.setValue)
                    self.thresholdSpinBox.valueChanged.connect(self.signalViewer.thresholdMarker.set_threshold)
                    QtGui.QApplication.restoreOverrideCursor()
                    # Update recent list
                    self.push_recent_list(filename)
                    # Update GUI
                    self.centralwidget.setVisible(True)
                    self.actionClose.setEnabled(True)
                    self.actionSelect_All.setEnabled(True)
                    self.actionCreate_New_Event.setEnabled(True)
                    self.actionSTA_LTA.setEnabled(True)
                    self.actionAMPA.setEnabled(True)
                    self.actionPlay.setEnabled(True)
                    self.toolBarNavigation.setEnabled(True)
                    self.toolBarAnalysis.setEnabled(True)
                    self.set_title()
            else:
                other = MainWindow(filename=filename)
                MainWindow.windowList.append(other)
                other.move(self.x() + 40, self.y() + 40)
                other.show()

    def open_recent(self):
        """Opens a document from recent opened list."""
        action = self.sender()
        if action:
            self.open(action.data())

    def save(self):
        """Saves a results summary to file.

        If summary has not been saved yet, opens a save file dialog.
        """
        if self.saved_filename is None:
            return self.save_as()
        else:
            return self.save_events(self.saved_filename)

    def save_as(self):
        """Opens a save file dialog to save a summary to file."""
        filename, _ = QtGui.QFileDialog.getSaveFileName(self, "Open Data File", ".",
                                                        "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)")
        if filename != '':
            self.save_events(filename)

    def save_events(self, filename):
        """Saves a results summary to file.

        Generates a results CSV summary.

        Args:
            filename: Output file name.
        """
        with open(filename, 'w') as f:
            rc.generate_csv([self.record], f)
            self.saved_filename = filename

    def close(self):
        """Closes current document.

        If there are any changes to save, shows a dialog asking
        the user whether to save data or not.
        """
        if self.maybeSave():
            self.record = None
            self._model.emptyList.disconnect(self.set_modified)
            self._model = None
            self.set_modified(False)
            self.saved_filename = None
            self.signalViewer.thresholdMarker.thresholdChanged.disconnect(self.thresholdSpinBox.setValue)
            self.thresholdSpinBox.valueChanged.disconnect(self.signalViewer.thresholdMarker.set_threshold)
            # Update GUI
            self.centralwidget.setVisible(False)
            self.actionClose.setEnabled(False)
            self.actionSelect_All.setEnabled(False)
            self.actionCreate_New_Event.setEnabled(False)
            self.actionSTA_LTA.setEnabled(False)
            self.actionAMPA.setEnabled(False)
            self.actionPlay.setEnabled(False)
            self.toolBarNavigation.setEnabled(False)
            self.toolBarAnalysis.setEnabled(False)
            self.set_title()

    def edit_settings(self):
        """Opens settings dialog."""
        dialog = settingsdialog.SettingsDialog(self)
        dialog.exec_()

    def push_recent_list(self, filename):
        """Adds a document to recent opened list.

        Args:
            filename: Name of the file to add.
        """
        settings = QtCore.QSettings(_organization, _application_name)
        files = self.get_recent_list()
        if filename in files:
            files.remove(filename)
        files.insert(0, filename)
        settings.setValue('recentFileList', files)
        self.set_recent_menu()

    def get_recent_list(self):
        """Gets a list of recent opened documents.

        Returns:
            out: A list of filenames.
        """
        settings = QtCore.QSettings(_organization, _application_name)
        files = settings.value('recentFileList')
        if files:
            if isinstance(files, list):
                return list(files)
            else:
                return [files]
        return []

    def clear_recent_list(self):
        """Clears recent opened documents list."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.setValue('recentFileList', [])
        self.set_recent_menu()

    def set_recent_menu(self):
        """Fills 'File -> Open Recent' menu with a list of recent opened
        docs.
        """
        files = self.get_recent_list()
        files_no = len(files)
        num_recent_files = min(files_no, MainWindow.MaxRecentFiles)

        self.menuOpen_Recent.clear()
        for i in xrange(num_recent_files):
            action = QtGui.QAction("&%d %s" %
                                   (i + 1, self.strippedName(files[i])), self)
            action.setData(files[i])
            action.triggered.connect(self.open_recent)
            self.menuOpen_Recent.addAction(action)
        self.menuOpen_Recent.addSeparator()
        self.menuOpen_Recent.addAction(self.actionClearRecent)
        if num_recent_files == 0:
            self.actionClearRecent.setEnabled(False)
        else:
            self.actionClearRecent.setEnabled(True)

    def maybeSave(self):
        """If there are any changes to save, shows a dialog asking
        the user whether to save data or not.

        Returns:
            out: If the user cancels the dialog returns True, otherwise returns
                True.
        """
        if self.isModified:
            ret = QtGui.QMessageBox.warning(self, "Save changes",
                    "The document has been modified.\nDo you want to save "
                    "your changes?",
                    QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard |
                    QtGui.QMessageBox.Cancel)
            if ret == QtGui.QMessageBox.Save:
                self.save()
            elif ret == QtGui.QMessageBox.Cancel:
                return False
        return True

    def closeEvent(self, event):
        """Current window's close event"""
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def set_modified(self, value):
        """Sets 'isModified' attribute's value"""
        self.isModified = value
        self.actionSave.setEnabled(value)
        self.actionSave_As.setEnabled(value)
        self.actionGenerate_HTML.setEnabled(value)

    def set_title(self):
        """Sets current window's title."""
        prefix = '' if self.record is None else "%s - " % self.record.filename
        self.setWindowTitle('%sP-phase Picker v.%s' % (prefix, __version__))

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

    def toogle_threshold(self, value):
        """Set threshold checkbox's value"""
        self.thresholdLabel.setEnabled(value)
        self.thresholdSpinBox.setEnabled(value)
        self.signalViewer.thresholdMarker.set_visible(value)

    def onPickingFinished(self):
        """Updates current window after performing an event
        detection/picking analysis."""
        self.signalViewer.set_record(self.record)
        self.signalViewer.thresholdMarker.thresholdChanged.connect(self.thresholdSpinBox.setValue)
        self.thresholdSpinBox.valueChanged.connect(self.signalViewer.thresholdMarker.set_threshold)
        self.signalViewer.thresholdMarker.set_threshold(self.thresholdSpinBox.value())
        self.signalViewer.thresholdMarker.set_visible(self.thresholdCheckBox.checkState())
        nevents = len(self.record.events)
        self._model.updateList()
        msgBox = QtGui.QMessageBox()
        msgBox.setText("%s possible event(s) has been found" % nevents)
        msgBox.exec_()

    def doSTALTA(self):
        """Performs event detection/picking by using STA-LTA method."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup('stalta_settings')
        sta_length = float(settings.value('sta_window_len', 5.0))
        lta_length = float(settings.value('lta_window_len', 100.0))
        settings.endGroup()
        if self.thresholdCheckBox.checkState():
            threshold = self.thresholdSpinBox.value()
        else:
            threshold = None
        alg = stalta.StaLta(sta_length, lta_length)
        return_code = pickingtaskdialog.PickingTaskDialog(self.record, alg, threshold).exec_()
        if return_code == QtGui.QDialog.Accepted:
            self.onPickingFinished()

    def doAMPA(self):
        """Performs event detection/picking by using AMPA method."""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup('ampa_settings')
        wlen = float(settings.value('window_len', 100.0))
        woverlap = float(settings.value('overlap', 0.5))
        nthres = float(settings.value('noise_threshold', 90))
        filters = settings.value('ampa_settings/filters', [30.0, 20.0, 10.0,
                                                           5.0, 2.5])
        filters = list(filters) if isinstance(filters, list) else [filters]
        settings.beginGroup('filter_bank_settings')
        startf = float(settings.value('startf', 2.0))
        endf = float(settings.value('endf', 12.0))
        bandwidth = float(settings.value('bandwidth', 3.0))
        overlap = float(settings.value('overlap', 1.0))
        settings.endGroup()
        settings.endGroup()
        if self.thresholdCheckBox.checkState():
            threshold = self.thresholdSpinBox.value()
        else:
            threshold = None
        alg = ampa.Ampa(wlen, woverlap, filters, noise_thr=nthres,
                        bandwidth=bandwidth, overlap=overlap,
                        f_start=startf, f_end=endf)
        return_code = pickingtaskdialog.PickingTaskDialog(self.record, alg, threshold).exec_()
        if return_code == QtGui.QDialog.Accepted:
            self.onPickingFinished()

    def goToEventPosition(self, index):
        """Centers signal viewer widget to an event location.

        Args:
            index: Event row index at Events Table.
        """
        self.signalViewer.set_position(self.record.events[index.row()].time)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
