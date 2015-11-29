#!/usr/bin/python2.7
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

import matplotlib
matplotlib.rcParams['backend'] = 'qt4agg'
matplotlib.rcParams['backend.qt4'] = 'PySide'
matplotlib.rcParams['patch.antialiased'] = False
matplotlib.rcParams['agg.path.chunksize'] = 80000

import numpy as np
import traceback
import os

from apasvo.picking import stalta
from apasvo.picking import ampa
from apasvo.picking import apasvotrace as rc

from PySide import QtGui, QtCore

from apasvo._version import __version__
from apasvo._version import _application_name
from apasvo._version import _organization
from apasvo.gui.views.generated import ui_mainwindow
from apasvo.utils.formats import rawfile
from apasvo.gui.views.generated import qrc_icons
from apasvo.gui.delegates import cbdelegate
from apasvo.gui.models import pickingtask
from apasvo.gui.models import eventcommands as commands
from apasvo.gui.views import aboutdialog
from apasvo.gui.views import svwidget
from apasvo.gui.views import navigationtoolbar
from apasvo.gui.views import loaddialog
from apasvo.gui.views import savedialog
from apasvo.gui.views import save_events_dialog
from apasvo.gui.views import settingsdialog
from apasvo.gui.views import takanamidialog
from apasvo.gui.views import trace_selector_dialog
from apasvo.gui.views import staltadialog
from apasvo.gui.views import ampadialog
from apasvo.gui.views import playertoolbar
from apasvo.gui.views import error
from apasvo.gui.views import processingdialog


format_csv = 'csv'
format_xml = 'xml'
format_nlloc = 'hyp'
format_json = 'json'
format_other = 'other'

binary_files_filter = 'Binary Files (*.bin)'
text_files_filter = 'Text Files (*.txt)'
all_files_filter = 'All Files (*.*)'
csv_files_filter = 'CSV Files (*.csv)'
xml_files_filter = 'XML Files (*.xml)'
nlloc_files_filter = 'NLLoc Files (*.hyp)'
json_files_filter = 'JSON Files (*.json)'

APASVO_URL = 'https://github.com/jemromerol/apasvo/wiki'


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
    _summary_file_filters = {xml_files_filter: format_xml,
                             nlloc_files_filter: format_nlloc,
                             json_files_filter: format_json,
                             text_files_filter: rawfile.format_text,
                             all_files_filter: format_other}

    def __init__(self, parent=None, filename=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.stream = rc.ApasvoStream([])
        self.document_list = []
        self.current_document_idx = -1
        self.document = None
        self.isModified = False
        self.saved_filename = None
        self.saved_event_format = None
        self.saved_cf_filename = None
        self.saved_cf_format = None
        self.saved_cf_dtype = None
        self.saved_cf_byteorder = None

        # Create context menu for events table
        self.event_context_menu = QtGui.QMenu(self)
        self.event_context_menu.addAction(self.actionDelete_Selected)
        self.EventsTableView.customContextMenuRequested.connect(lambda: self.event_context_menu.exec_(QtGui.QCursor.pos()))
        self.EventsTableView.clicked.connect(self.goto_event_position)

        self.actionOpen.triggered.connect(self.load)
        self.actionSaveEvents.triggered.connect(self.save_events)
        self.actionSaveEvents_As.triggered.connect(self.save_events_as)
        self.actionSaveCF.triggered.connect(self.save_cf)
        self.actionSaveCF_As.triggered.connect(self.save_cf_as)
        self.actionClose.triggered.connect(lambda: self.command_stack.push(commands.CloseTraces(self, [self.current_document_idx])))
        self.actionQuit.triggered.connect(QtGui.qApp.closeAllWindows)
        self.actionClearRecent.triggered.connect(self.clear_recent_list)
        self.actionSettings.triggered.connect(self.edit_settings)
        self.actionSTA_LTA.triggered.connect(self.doSTALTA)
        self.actionAMPA.triggered.connect(self.doAMPA)
        self.actionTakanami.triggered.connect(self.doTakanami)
        self.actionClear_Event_List.triggered.connect(self.clear_events)
        self.actionDelete_Selected.triggered.connect(self.delete_selected_events)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionOnlineHelp.triggered.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(APASVO_URL)))

        # Create stream viewer dialog
        self.trace_selector = trace_selector_dialog.TraceSelectorDialog(self.stream, parent=self)
        self.action_show_trace_selector.toggled.connect(self.trace_selector.setVisible)
        self.trace_selector.closed.connect(lambda: self.action_show_trace_selector.setChecked(False))
        self.trace_selector.selection_changed.connect(self.toogle_document)

        # add navigation toolbar
        self.signalViewer = svwidget.SignalViewerWidget(self.splitter)
        self.splitter.addWidget(self.signalViewer)
        self.toolBarNavigation = navigationtoolbar.NavigationToolBar(self.signalViewer.canvas, self)
        self.toolBarNavigation.setEnabled(False)
        self.toolBarNavigation.view_restored.connect(self.signalViewer.subplots_adjust)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarNavigation)
        self.addToolBarBreak()
        # add analysis toolbar
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarAnalysis)
        self.addToolBarBreak()
        # add media toolbar
        settings = QtCore.QSettings(_organization, _application_name)
        settings.beginGroup('player_settings')
        fs = int(settings.value('playback_freq', playertoolbar.DEFAULT_REAL_FREQ))
        bd = settings.value('bit_depth', playertoolbar.DEFAULT_BIT_DEPTH)
        settings.endGroup()
        self.toolBarMedia = playertoolbar.PlayerToolBar(self, sample_freq=fs, bd=bd)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBarMedia)
        self.toolBarMedia.intervalChanged.connect(self.signalViewer.set_selector_limits)
        self.toolBarMedia.intervalSelected.connect(self.signalViewer.selector.set_active)
        self.toolBarMedia.tick.connect(self.signalViewer.set_playback_position)
        self.toolBarMedia.playingStateChanged.connect(lambda x: self.signalViewer.set_selection_enabled(not x))
        self.toolBarMedia.playingStateSelected.connect(lambda: self.signalViewer.set_playback_marker_visible(True))
        self.toolBarMedia.stoppedStateSelected.connect(lambda: self.signalViewer.set_playback_marker_visible(False))
        self.signalViewer.selector.toggled.connect(self.toolBarMedia.toggle_interval_selected)
        self.signalViewer.selector.valueChanged.connect(self.toolBarMedia.set_limits)
        self.addToolBarBreak()

        self.actionEvent_List.toggled.connect(self.EventsTableView.setVisible)

        self.actionSignal_Amplitude.toggled.connect(self.signalViewer.set_signal_amplitude_visible)
        self.actionSignal_Envelope.toggled.connect(self.signalViewer.set_signal_envelope_visible)
        self.actionEspectrogram.toggled.connect(self.signalViewer.set_espectrogram_visible)
        self.actionCharacteristic_Function.toggled.connect(self.signalViewer.set_cf_visible)
        self.actionSignal_MiniMap.toggled.connect(self.signalViewer.set_minimap_visible)
        self.signalViewer.selector.toggled.connect(self.on_selection_toggled)
        self.signalViewer.selector.valueChanged.connect(self.on_selection_changed)
        self.signalViewer.CF_loaded.connect(self.actionCharacteristic_Function.setEnabled)
        self.signalViewer.CF_loaded.connect(self.actionCharacteristic_Function.setChecked)
        self.signalViewer.event_selected.connect(self.on_event_picked)
        self.actionActivateThreshold.toggled.connect(self.toggle_threshold)

        self.actionMain_Toolbar.toggled.connect(self.toolBarMain.setVisible)
        self.actionMedia_Toolbar.toggled.connect(self.toolBarMedia.setVisible)
        self.actionAnalysis_Toolbar.toggled.connect(self.toolBarAnalysis.setVisible)
        self.actionNavigation_Toolbar.toggled.connect(self.toolBarNavigation.setVisible)

        # Connect trace selector to signal viewer
        self.trace_selector.detection_performed.connect(self.signalViewer.update_cf)

        self.set_title()
        self.set_recent_menu()

    def load(self, filename=None):
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
                                                            ";;".join(self._file_filters), all_files_filter)
        if filename != '':
            dialog = loaddialog.LoadDialog(self, filename)
            return_code = dialog.exec_()
            if return_code == QtGui.QDialog.Accepted:
                try:
                    values = dialog.get_values()
                    # Load and visualize the opened record
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                    self.analysis_label.setText("Loading {}...".format(os.path.basename(filename)))
                    self.analysis_progress_bar.show()
                    stream = rc.read(filename, **values)
                    self.command_stack.push(commands.OpenStream(self, stream))
                    # Update recent list
                    self.push_recent_list(filename)
                except Exception as e:
                    error.display_error_dlg(str(e), traceback.format_exc())
                finally:
                    self.analysis_progress_bar.hide()
                    self.analysis_label.setText("")
                    QtGui.QApplication.restoreOverrideCursor()


    def open_recent(self):
        """Opens a document from recent opened list."""
        action = self.sender()
        if action:
            self.load(action.data())

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
            # Show dialog
            dialog = save_events_dialog.SaveEventsDialog(self, fmt=self.saved_event_format)
            return_code = dialog.exec_()
            # Save Events to file and store settings
            if return_code == QtGui.QDialog.Accepted:
                values = dialog.get_values()
                self.save_event_list(filename, format=values.get('fmt'))

    def save_event_list(self, filename, **kwargs):
        """Saves a results summary to file.

        Generates a results CSV summary.

        Args:
            filename: Output file name.
        """
        rc.ApasvoStream([self.document.record]).export_picks(filename, **kwargs)
        self.saved_filename = filename
        self.saved_event_format = kwargs.get('format')

    def save_cf(self):
        """Saves characteristic function to file.

        If no characteristic function has been saved yet, opens a save file dialog.
        """
        if self.saved_cf_filename is None:
            return self.save_cf_as()
        else:
            return self.document.record.save_cf(self.saved_cf_filename,
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
                self.document.record.save_cf(filename, **values)
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
            if self.document is not None:
                # Disconnect all signals!!
                self.document = None
            self.set_modified(False)
            self.saved_filename = None
            self.saved_event_format = None
            self.signalViewer.unset_record()
            self.toolBarMedia.disconnect_path()
            # Update GUI
            self.centralwidget.setVisible(False)
            self.actionClose.setEnabled(False)
            self.actionClear_Event_List.setEnabled(False)
            self.actionSTA_LTA.setEnabled(False)
            self.actionAMPA.setEnabled(False)
            self.toolBarNavigation.setEnabled(False)
            self.toolBarAnalysis.setEnabled(False)
            self.adjustSize()
            self.set_title()

    def toogle_document(self, document_idx):
        """

        :param document:
        :return:
        """
        self.current_document_idx = document_idx
        document = self.document_list[document_idx]
        if document != self.document:
            self.disconnect_document()
            # Load and visualize the opened record
            self.document = document
            self.document.emptyList.connect(self.set_modified)
            ########
            self.EventsTableView.setModel(self.document)
            model = self.EventsTableView.selectionModel()
            model.selectionChanged.connect(self.on_event_selection)
            # Connect Delegates
            for i, attribute in enumerate(self.document.attributes):
                if attribute.get('attribute_type') == 'enum' and attribute.get('editable', False):
                    delegate = cbdelegate.ComboBoxDelegate(self.EventsTableView,
                                                           attribute.get('value_list', []))
                    self.EventsTableView.setItemDelegateForColumn(i, delegate)
                else:
                    self.EventsTableView.setItemDelegateForColumn(i, None)
            # connect trace selector to document
            self.trace_selector.events_created.connect(lambda x: self.document.updateList())
            self.trace_selector.events_deleted.connect(lambda x: self.document.updateList())
            self.trace_selector.events_created.connect(self.signalViewer.create_events)
            self.trace_selector.events_deleted.connect(self.signalViewer.delete_events)
            # connect document model to signalViewer
            self.document.eventCreated.connect(self.signalViewer.create_event)
            self.document.eventCreated.connect(self.trace_selector.update_events)
            self.document.eventDeleted.connect(self.signalViewer.delete_event)
            self.document.eventDeleted.connect(self.trace_selector.update_events)
            self.document.eventModified.connect(self.signalViewer.update_event)
            self.document.eventModified.connect(self.trace_selector.update_events)
            self.document.detectionPerformed.connect(self.signalViewer.update_cf)
            self.document.detectionPerformed.connect(self.toolBarNavigation.update)
            # load document data into signal viewer
            self.signalViewer.unset_record()
            self.signalViewer.set_record(self.document)
            self.signalViewer.thresholdMarker.thresholdChanged.connect(self.thresholdSpinBox.setValue)
            self.signalViewer.set_signal_amplitude_visible(self.actionSignal_Amplitude.isChecked())
            self.signalViewer.set_signal_envelope_visible(self.actionSignal_Envelope.isChecked())
            self.signalViewer.set_cf_visible(self.actionCharacteristic_Function.isChecked())
            self.signalViewer.set_espectrogram_visible(self.actionEspectrogram.isChecked())
            self.signalViewer.set_minimap_visible(self.actionSignal_MiniMap.isChecked())
            self.signalViewer.set_threshold_visible(self.actionActivateThreshold.isChecked())
            self.signalViewer.thresholdMarker.set_threshold(self.thresholdSpinBox.value())
            self.thresholdSpinBox.valueChanged.connect(self.signalViewer.thresholdMarker.set_threshold)
            self.toolBarMedia.load_data(self.document.record.signal, self.document.record.fs)
            self.toolBarMedia.connect_path()
            # Update GUI
            self.centralwidget.setVisible(True)
            self.actionClose.setEnabled(True)
            self.actionClear_Event_List.setEnabled(True)
            self.actionSTA_LTA.setEnabled(True)
            self.actionAMPA.setEnabled(True)
            self.toolBarNavigation.setEnabled(True)
            self.toolBarAnalysis.setEnabled(True)
            self.toolBarMedia.set_enabled(True)
            self.set_title()

    def disconnect_document(self):
        if self.document is not None:
            # Disconnect existing signals
            self.trace_selector.events_created.disconnect()
            self.trace_selector.events_deleted.disconnect()
            # Disconnect document signal
            self.document.emptyList.disconnect(self.set_modified)
            self.document.eventCreated.disconnect()
            self.document.eventDeleted.disconnect()
            self.document.eventModified.disconnect()
            self.document.detectionPerformed.disconnect(self.signalViewer.update_cf)
            self.document.detectionPerformed.disconnect(self.toolBarNavigation.update)
            model = self.EventsTableView.selectionModel()
            model.selectionChanged.disconnect(self.on_event_selection)

    def edit_settings(self):
        """Opens settings dialog."""
        dialog = settingsdialog.SettingsDialog(self)
        dialog.saved.connect(self.update_settings)
        dialog.exec_()

    def update_settings(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        settings = QtCore.QSettings(_organization, _application_name)
        # update player settings
        settings.beginGroup('player_settings')
        fs = int(settings.value('playback_freq', playertoolbar.DEFAULT_REAL_FREQ))
        bd = settings.value('bit_depth', playertoolbar.DEFAULT_BIT_DEPTH)
        settings.endGroup()
        self.toolBarMedia.set_audio_format(fs, bd)
        # update event colors
        if self.document is not None:
            self.document.loadColorMap()
        # update spectrogram
        if self.signalViewer is not None:
            self.signalViewer.update_specgram_settings()
        QtGui.QApplication.restoreOverrideCursor()

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
            # prevent toolBarMedia firing signals if it's on playing or paused state
            self.toolBarMedia.blockSignals(True)
            self.toolBarMedia.disconnect_path()
            event.accept()
        else:
            event.ignore()

    def set_modified(self, value):
        """Sets 'isModified' attribute's value"""
        self.isModified = value
        self.actionSaveEvents.setEnabled(value)
        self.actionSaveEvents_As.setEnabled(value)
        # If already computed, enable save CF
        cf_computed = False if self.document is None else len(self.document.record.cf) != 0
        self.actionSaveCF.setEnabled(cf_computed)
        self.actionSaveCF_As.setEnabled(cf_computed)

    def set_title(self):
        """Sets current window's title."""
        prefix = '' if self.document is None else "%s - " % self.document.record.name
        self.setWindowTitle('%s%s v.%s' % (prefix, _application_name, __version__))

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

    def toggle_threshold(self, value):
        """Set threshold checkbox's value"""
        self.thresholdLabel.setEnabled(value)
        self.thresholdSpinBox.setEnabled(value)
        self.signalViewer.thresholdMarker.set_visible(value)

    def doSTALTA(self):
        """Performs event detection/picking by using STA-LTA method."""
        dialog = staltadialog.StaLtaDialog(self.stream,
                                           trace_list=[self.document.record])
        return_code = dialog.exec_()
        if return_code == QtGui.QDialog.Accepted:
            # Read settings
            settings = QtCore.QSettings(_organization, _application_name)
            settings.beginGroup('stalta_settings')
            sta_length = float(settings.value('sta_window_len', 5.0))
            lta_length = float(settings.value('lta_window_len', 100.0))
            settings.endGroup()
            # Get threshold value
            if self.actionActivateThreshold.isChecked():
                threshold = self.thresholdSpinBox.value()
            else:
                threshold = None
            # Create an STA-LTA algorithm instance with selected settings
            alg = stalta.StaLta(sta_length, lta_length)
            # perform task
            self._analysis_task = pickingtask.PickingTask(self.document, alg,
                                                                threshold)
            self.launch_analysis_task(self._analysis_task,
                                      label="Applying %s..." % alg.__class__.__name__.upper())

    def doAMPA(self):
        """Performs event detection/picking by using AMPA method."""
        dialog = ampadialog.AmpaDialog(self.stream,
                                       trace_list=[self.document.record])
        return_code = dialog.exec_()
        if return_code == QtGui.QDialog.Accepted:
            # Read settings
            settings = QtCore.QSettings(_organization, _application_name)
            settings.beginGroup('ampa_settings')
            wlen = float(settings.value('window_len', 100.0))
            wstep = float(settings.value('step', 50.0))
            nthres = float(settings.value('noise_threshold', 90))
            filters = settings.value('filters', [30.0, 20.0, 10.0,
                                                               5.0, 2.5])
            filters = list(filters) if isinstance(filters, list) else [filters]
            filters = np.array(filters).astype(float)
            settings.beginGroup('filter_bank_settings')
            startf = float(settings.value('startf', 2.0))
            endf = float(settings.value('endf', 12.0))
            bandwidth = float(settings.value('bandwidth', 3.0))
            overlap = float(settings.value('overlap', 1.0))
            settings.endGroup()
            settings.endGroup()
            # Get threshold value
            if self.actionActivateThreshold.isChecked():
                threshold = self.thresholdSpinBox.value()
            else:
                threshold = None
            # Create an AMPA algorithm instance with selected settings
            alg = ampa.Ampa(wlen, wstep, filters, noise_thr=nthres,
                            bandwidth=bandwidth, overlap=overlap,
                            f_start=startf, f_end=endf)
            # perform task
            self._analysis_task = pickingtask.PickingTask(self.document, alg,
                                                                threshold)
            self.launch_analysis_task(self._analysis_task,
                                      label="Applying %s..." % alg.__class__.__name__.upper())

    def launch_analysis_task(self, task, label=""):
        wait_dialog = processingdialog.ProcessingDialog(label_text=label)
        wait_dialog.setWindowTitle("Event detection")
        wait_dialog.run(task)

    def doTakanami(self):
        xleft, xright = self.signalViewer.get_selector_limits()
        takanamidialog.TakanamiDialog(self.document, xleft, xright).exec_()

    def clear_events(self):
        if self.document is not None:
            self.document.clearEvents()

    def delete_selected_events(self):
        if self.document is not None:
            selected_rows = self.EventsTableView.selectionModel().selectedRows()
            self.document.removeRows([row.row() for row in selected_rows])

    def goto_event_position(self, index):
        self.signalViewer.goto_event(self.document.record.events[index.row()])

    def on_event_selection(self, s, d):
        selected_events = [self.document.getEventByRow(index.row())
                           for index in self.EventsTableView.selectionModel().selectedRows()]
        self.actionDelete_Selected.setEnabled(len(selected_events) > 0)
        self.signalViewer.set_event_selection(selected_events)

    def on_event_picked(self, event):
        if self.document is not None:
            self.EventsTableView.selectionModel().clear()
            self.EventsTableView.selectionModel().select(self.document.index(self.document.indexOf(event), 0),
                                                         QtGui.QItemSelectionModel.ClearAndSelect |
                                                         QtGui.QItemSelectionModel.Rows)

    def on_selection_toggled(self, value):
        self.on_selection_changed(*self.signalViewer.get_selector_limits())

    def on_selection_changed(self, xleft, xright):
        selection_length = abs(xleft - xright)
        enable_takanami = (self.signalViewer.selector.active and
                           (selection_length >= (takanamidialog.MINIMUM_MARGIN_IN_SECS * 2)))
        self.actionTakanami.setEnabled(enable_takanami)

    def show_about(self):
        aboutdialog.AboutDialog(self).exec_()
