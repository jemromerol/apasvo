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
from gui.views import navigationtoolbar
from gui.views import loaddialog
from gui.views import savedialog
from gui.views import settingsdialog
from gui.views import pickingtaskdialog
from gui.views import playertoolbar
from gui.views import eventposdialog

from picking import stalta
from picking import ampa
from picking import record as rc
from utils.formats import rawfile

from _version import __version__
from _version import _application_name
from _version import _organization


format_csv = 'csv'
format_other = 'other'

binary_files_filter = 'Binary Files (*.bin)'
text_files_filter = 'Text Files (*.txt)'
all_files_filter = 'All Files (*.*)'
csv_files_filter = 'CSV Files (*.csv)'


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

    _file_filters = {binary_files_filter: rawfile.format_binary,
                        text_files_filter: rawfile.format_text,
                        all_files_filter: format_other}
    _cf_file_filters = {binary_files_filter: rawfile.format_binary,
                        text_files_filter: rawfile.format_text,
                        all_files_filter: format_other}
    _summary_file_filters = {csv_files_filter: format_csv,
                             text_files_filter: rawfile.format_text,
                             all_files_filter: format_other}

    def __init__(self, parent=None, filename=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.record = None
        self._model = None
        self.isModified = False
        self.saved_filename = None
        self.saved_cf_filename = None
        self.saved_cf_format = None
        self.saved_cf_dtype = None
        self.saved_cf_byteorder = None

        stateDelegate = cbdelegate.ComboBoxDelegate(self.EventsTableView, rc.Event.statuses)
        self.EventsTableView.setItemDelegateForColumn(5, stateDelegate)
        self.EventsTableView.clicked.connect(self.goToEventPosition)
        self.EventsTableView.clicked.connect(self.on_event_selection)

        self.actionOpen.triggered.connect(self.open)
        self.actionSave.triggered.connect(self.save_events)
        self.actionSave.triggered.connect(self.save_cf)
        self.actionSave_As.triggered.connect(self.save_events_as)
        self.actionSave_As.triggered.connect(self.save_cf_as)
        self.actionSaveEvents.triggered.connect(self.save_events)
        self.actionSaveEvents_As.triggered.connect(self.save_events_as)
        self.actionSaveCF.triggered.connect(self.save_cf)
        self.actionSaveCF_As.triggered.connect(self.save_cf_as)
        self.actionClose.triggered.connect(self.close)
        self.actionQuit.triggered.connect(QtGui.qApp.closeAllWindows)
        self.actionClearRecent.triggered.connect(self.clear_recent_list)
        self.actionSettings.triggered.connect(self.edit_settings)
        self.actionSTA_LTA.triggered.connect(self.doSTALTA)
        self.actionAMPA.triggered.connect(self.doAMPA)
        self.actionEdit_Event.triggered.connect(self.edit_event)
        self.actionClear_Event_List.triggered.connect(self.clear_events)
        # add navigation toolbar
        self.signalViewer = svwidget.SignalViewerWidget(self.splitter)
        self.splitter.addWidget(self.signalViewer)
        self.toolBarNavigation = navigationtoolbar.NavigationToolBar(self.signalViewer.canvas, self)
        self.toolBarNavigation.setEnabled(False)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarNavigation)
        self.addToolBarBreak()
        # add analysis toolbar
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarAnalysis)
        self.addToolBarBreak()
        # add media toolbar
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup('player_settings')
        fs = int(settings.value('sample_rate', playertoolbar.sample_rates[0]))
        bd = settings.value('bit_depth', playertoolbar.bit_depths[1])
        settings.endGroup()
        self.toolBarMedia = playertoolbar.PlayerToolBar(self, fs=fs, bd=bd)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarMedia)
        self.toolBarMedia.intervalChanged.connect(self.signalViewer.set_selector_limits)
        self.toolBarMedia.intervalSelected.connect(self.signalViewer.selector.set_active)
        self.signalViewer.selector.toggled.connect(self.toolBarMedia.toggle_interval_selected)
        self.signalViewer.selector.valueChanged.connect(self.toolBarMedia.set_limits)
        self.addToolBarBreak()

        self.actionEvent_List.toggled.connect(self.EventsTableView.setVisible)
        self.actionSignal_Amplitude.toggled.connect(self.signalViewer.set_signal_amplitude_visible)
        self.actionSignal_Envelope.toggled.connect(self.signalViewer.set_signal_envelope_visible)
        self.actionEspectrogram.toggled.connect(self.signalViewer.set_espectrogram_visible)
        self.actionCharacteristic_Function.toggled.connect(self.signalViewer.set_cf_visible)
        self.actionSignal_MiniMap.toggled.connect(self.signalViewer.set_minimap_visible)
        self.signalViewer.selector.toggled.connect(self.actionTakanami.setEnabled)
        self.thresholdCheckBox.toggled.connect(self.toggle_threshold)
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
                                                            ";;".join(self._file_filters))
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
                    self.toolBarMedia.load_data(self.record.signal, self.record.fs)
                    self.toolBarMedia.connect_path()
                    QtGui.QApplication.restoreOverrideCursor()
                    # Update recent list
                    self.push_recent_list(filename)
                    # Update GUI
                    self.centralwidget.setVisible(True)
                    self.actionClose.setEnabled(True)
                    self.actionSelect_All.setEnabled(True)
                    self.actionCreate_New_Event.setEnabled(True)
                    self.actionClear_Event_List.setEnabled(True)
                    self.actionSTA_LTA.setEnabled(True)
                    self.actionAMPA.setEnabled(True)
                    self.toolBarNavigation.setEnabled(True)
                    self.toolBarAnalysis.setEnabled(True)
                    self.toolBarMedia.set_enabled(True)
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

    def save_events(self):
        """Saves event list to file.

        If no events has been saved yet, opens a save file dialog.
        """
        if self.saved_filename is None:
            return self.save_events_as()
        else:
            return self.save_event_list(self.saved_filename)

    def save_events_as(self):
        """Opens a save file dialog to save event list to file."""
        filename, _ = QtGui.QFileDialog.getSaveFileName(self, "Save Event List to File", ".",
                                                        ";;".join(self._summary_file_filters))
        if filename != '':
            self.save_event_list(filename)

    def save_event_list(self, filename):
        """Saves a results summary to file.

        Generates a results CSV summary.

        Args:
            filename: Output file name.
        """
        with open(filename, 'w') as f:
            rc.generate_csv([self.record], f)
            self.saved_filename = filename

    def save_cf(self):
        """Saves characteristic function to file.

        If no characteristic function has been saved yet, opens a save file dialog.
        """
        if self.saved_cf_filename is None:
            return self.save_cf_as()
        else:
            return self.record.save_cf(self.saved_cf_filename,
                                       fmt=self.saved_cf_format,
                                       dtype=self.saved_cf_dtype,
                                       byteorder=self.saved_cf_byteorder)

    def save_cf_as(self):
        """Open a save file dialog to save computed characteristic function."""
        filename, selected_filter = QtGui.QFileDialog.getSaveFileName(self, "Save Characteristic Function to File", ".",
                                                        ";;".join(self._cf_file_filters.keys()))
        if filename != '':
            # Set defaults
            if self._cf_file_filters[selected_filter] != format_other:
                fmt = self._cf_file_filters[selected_filter]
            elif self.saved_cf_format is not None:
                fmt = self.saved_cf_format
            else:
                fmt = rawfile.format_binary
            if self.saved_cf_dtype is not None:
                dtype = self.saved_cf_dtype
            else:
                dtype = rawfile.datatype_float64
            if self.saved_cf_byteorder is not None:
                byteorder = self.saved_cf_byteorder
            else:
                byteorder = rawfile.byteorder_native
            # Show dialog
            dialog = savedialog.SaveDialog(self, fmt=fmt,
                                           dtype=dtype,
                                           byteorder=byteorder)
            return_code = dialog.exec_()
            # Save CF to file and store settings
            if return_code == QtGui.QDialog.Accepted:
                values = dialog.get_values()
                self.record.save_cf(filename, **values)
                self.saved_cf_filename = filename
                self.saved_cf_format = values['fmt']
                self.saved_cf_dtype = values['dtype']
                self.saved_cf_byteorder = values['byteorder']

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
            self.toolBarMedia.disconnect_path()
            # Update GUI
            self.centralwidget.setVisible(False)
            self.actionClose.setEnabled(False)
            self.actionSelect_All.setEnabled(False)
            self.actionCreate_New_Event.setEnabled(False)
            self.actionClear_Event_List.setEnabled(False)
            self.actionSTA_LTA.setEnabled(False)
            self.actionAMPA.setEnabled(False)
            self.toolBarNavigation.setEnabled(False)
            self.toolBarAnalysis.setEnabled(False)
            self.set_title()

    def edit_settings(self):
        """Opens settings dialog."""
        dialog = settingsdialog.SettingsDialog(self)
        dialog.saved.connect(self.update_settings)
        dialog.exec_()

    def update_settings(self):
        settings = QtCore.QSettings(_organization, _application_name)
        # update player settings
        settings.beginGroup('player_settings')
        fs = int(settings.value('sample_rate', playertoolbar.sample_rates[0]))
        bd = settings.value('bit_depth', playertoolbar.bit_depths[1])
        self.toolBarMedia.set_audio_format(fs, bd)

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
                self.save_events()
                self.save_cf()
            elif ret == QtGui.QMessageBox.Cancel:
                return False
        return True

    def closeEvent(self, event):
        """Current window's close event"""
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()
        self.toolBarMedia.disconnect_path()

    def set_modified(self, value):
        """Sets 'isModified' attribute's value"""
        self.isModified = value
        self.actionSave.setEnabled(value)
        self.actionSave_As.setEnabled(value)
        self.actionSaveEvents.setEnabled(value)
        self.actionSaveEvents_As.setEnabled(value)
        self.actionSaveCF.setEnabled(value)
        self.actionSaveCF_As.setEnabled(value)

    def set_title(self):
        """Sets current window's title."""
        prefix = '' if self.record is None else "%s - " % self.record.filename
        self.setWindowTitle('%sP-phase Picker v.%s' % (prefix, __version__))

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

    def toggle_threshold(self, value):
        """Set threshold checkbox's value"""
        self.thresholdLabel.setEnabled(value)
        self.thresholdSpinBox.setEnabled(value)
        self.signalViewer.thresholdMarker.set_visible(value)

    def onPickingFinished(self, n_events):
        """Updates current window after performing an event
        detection/picking analysis.

        Args:
            n_events: Number of events found.
        """
        self.signalViewer.set_record(self.record)
        self.signalViewer.thresholdMarker.thresholdChanged.connect(self.thresholdSpinBox.setValue)
        self.thresholdSpinBox.valueChanged.connect(self.signalViewer.thresholdMarker.set_threshold)
        self.signalViewer.thresholdMarker.set_threshold(self.thresholdSpinBox.value())
        self.signalViewer.thresholdMarker.set_visible(self.thresholdCheckBox.checkState())
        self._model.updateList()
        msgBox = QtGui.QMessageBox()
        msgBox.setText("%s possible event(s) has been found" % n_events)
        msgBox.exec_()

    def doSTALTA(self):
        """Performs event detection/picking by using STA-LTA method."""
        # Read settings
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup('stalta_settings')
        sta_length = float(settings.value('sta_window_len', 5.0))
        lta_length = float(settings.value('lta_window_len', 100.0))
        settings.endGroup()
        # Get threshold value
        if self.thresholdCheckBox.checkState():
            threshold = self.thresholdSpinBox.value()
        else:
            threshold = None
        # Create an STA-LTA algorithm instance with selected settings
        alg = stalta.StaLta(sta_length, lta_length)
        n_events = len(self.record.events)  # Number of events before picking
        return_code = pickingtaskdialog.PickingTaskDialog(self.record, alg, threshold).exec_()
        if return_code == QtGui.QDialog.Accepted:
            n_events_found = len(self.record.events) - n_events  # N. of events found
            self.onPickingFinished(n_events_found)

    def doAMPA(self):
        """Performs event detection/picking by using AMPA method."""
        # Read settings
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup('ampa_settings')
        wlen = float(settings.value('window_len', 100.0))
        wstep = float(settings.value('step', 50.0))
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
        # Get threshold value
        if self.thresholdCheckBox.checkState():
            threshold = self.thresholdSpinBox.value()
        else:
            threshold = None
        # Create an AMPA algorithm instance with selected settings
        alg = ampa.Ampa(wlen, wstep, filters, noise_thr=nthres,
                        bandwidth=bandwidth, overlap=overlap,
                        f_start=startf, f_end=endf)
        n_events = len(self.record.events)  # Number of events before picking
        return_code = pickingtaskdialog.PickingTaskDialog(self.record, alg, threshold).exec_()
        if return_code == QtGui.QDialog.Accepted:
            n_events_found = len(self.record.events) - n_events  # N. of events found
            self.onPickingFinished(n_events_found)

    def goToEventPosition(self, index):
        """Centers signal viewer widget to an event location.

        Args:
            index: Event row index at Events Table.
        """
        self.signalViewer.set_position(self.record.events[index.row()].time / self.record.fs)

    def clear_events(self):
        for event in self.record.events:
            self.signalViewer.delete_event(event)
        self.record.events = []
        self._model.updateList()

    def on_event_selection(self, index):
        n_selected = len(self.EventsTableView.selectionModel().selectedRows())
        self.actionDelete_Selected.setEnabled(n_selected > 0)
        self.actionEdit_Event.setEnabled(n_selected == 1)

    def edit_event(self):
        event = self.record.events[self.EventsTableView.selectionModel().
                                   selectedRows()[0].row()]
        eventposdialog.EventPosDialog(self.record, event, self).exec_()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(_application_name)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
