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
import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np
import datetime

from gui import ui_settingsdialog
from gui import ui_mainwindow
from gui import ui_loaddialog

from _version import __version__
from utils import futils
from utils.formats import rawfile
from picking import stalta
from picking import ampa
from picking import envelope as env
from picking import record as rc

_organization = 'UGR'
_application_name = 'P-phase Picker'


class ComboBoxDelegate(QtGui.QStyledItemDelegate):
    """
    """

    def __init__(self, parent=None, values=None):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        if values is None:
            values = []
        self._values = values

    def createEditor(self, parent, option, index):
        editor = QtGui.QComboBox(parent)
        editor.addItems(self._values)
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, comboBox, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole)
        try:
            comboBox.setCurrentIndex(self._values.index(value))
        except:
            comboBox.setCurrentIndex(0)

    def setModelData(self, comboBox, model, index):
        value = comboBox.currentText()
        model.setData(index, value)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class DoubleSpinBoxDelegate(QtGui.QStyledItemDelegate):
    """"""

    def __init__(self, parent=None, minimum=0.0, maximum=100.0, step=0.01):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self._min = minimum
        self._max = maximum
        self._step = step

    def createEditor(self, parent, option, index):
        editor = QtGui.QDoubleSpinBox(parent)
        editor.setMinimum(self._min)
        editor.setMaximum(self._max)
        editor.setSingleStep(self._step)
        editor.setAccelerated(True)
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole)
        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        value = spinBox.value()
        model.setData(index, value)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class EventListModel(QtCore.QAbstractTableModel):
    """
    """

    emptyList = QtCore.Signal(bool)

    def __init__(self, record, header):
        QtCore.QAbstractTableModel.__init__(self)
        self._record = record
        self._list = self._record.events
        self._header = header
        self.empty = (len(self._list) != 0)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        attr_name = self._header[index.column()]
        data = self._list[index.row()].__getattribute__(attr_name)
        if attr_name == 'time':
            return str(datetime.timedelta(seconds=data))
        if attr_name == 'cf_value':
            return "%.3f" % data
        return "%s" % data

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._header[section].replace('_', ' ').title()
        return None

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._record.sort_events(key=self._header[column],
                                 reverse=(order == QtCore.Qt.DescendingOrder))
        self._list = self._record.events
        self.layoutChanged.emit()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            self._list[index.row()].__setattr__(self._header[index.column()], value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        attr_name = self._header[index.column()]
        if attr_name in ['time', 'cf_value', 'mode', 'method']:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        return (QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsEnabled)

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        if row < 0 or row > len(self._list):
            return
        self.beginRemoveRows(parent, row, row + count - 1)
        while count != 0:
            del self._list[row]
            count -= 1
        self._setEmpty()
        self.endRemoveRows()

    def addEvent(self, event):
        """"""
        self.beginInsertRows(QtCore.QModelIndex(), len(self._list),
                             len(self._list))
        self._list.append(event)
        self._setEmpty()
        self.endInsertRows()

    def _setEmpty(self):
        """"""
        empty = (len(self._list) != 0)
        if self.empty != empty:
            self.empty = empty
            self.emptyList.emit(empty)

    def updateList(self):
        """"""
        self.modelAboutToBeReset.emit()
        self._list = self._record.events
        self._setEmpty()
        self.modelReset.emit()


class SpanSelector(QtCore.QObject):
    """
    """

    toogled = QtCore.Signal(bool)
    valueChanged = QtCore.Signal(float, float)

    def __init__(self, fig, xmin=0.0, xmax=0.0, minstep=0.01):
        super(SpanSelector, self).__init__()
        self.fig = fig
        self.xleft = 0.0
        self.xright = 0.0
        self.xmin = xmin
        self.xmax = xmax
        self.active = False
        self.minstep = minstep

        self.selectors = [ax.axvspan(0, 1, fc='LightCoral', ec='r', alpha=0.5)
                          for ax in self.fig.axes]
        for s in self.selectors:
            s.set_visible(False)

        bbox = dict(boxstyle="round", fc="LightCoral", ec="r", alpha=0.8)
        self.selectorLabel = matplotlib.text.Text(0, 0, "0.00", bbox=bbox)
        self.selectorLabel.set_visible(False)
        self.pick_threshold = None

        self.press_selector = None
        self.fig.canvas.mpl_connect('button_press_event', self.onpress)
        self.fig.canvas.mpl_connect('button_release_event', self.onrelease)
        self.fig.canvas.mpl_connect('motion_notify_event', self.onmove)

    def onpress(self, event):
        if not self.fig.canvas.widgetlock.locked():
            self.fig.canvas.widgetlock(self)
            if self.active:
                self.set_active(False)
            self.press_selector = event
            self.fig.canvas.draw_idle()

    def onrelease(self, event):
        if self.fig.canvas.widgetlock.isowner(self):
            self.press_selector = None
            self.fig.canvas.draw_idle()
            self.fig.canvas.widgetlock.release(self)

    def onmove(self, event):
        if self.press_selector is not None:
            xleft = round(self.get_xdata(self.press_selector), 3)
            xright = round(self.get_xdata(event), 3)
            if xright < xleft:
                xleft, xright = xright, xleft
            if xright - xleft >= self.minstep:
                if not self.active:
                    self.set_active(True)
                self.set_selector_limits(xleft, xright)

    def get_xdata(self, event):
        inv = self.fig.axes[0].transData.inverted()
        xdata, _ = inv.transform((event.x, event.y))
        return xdata

    def set_selector_limits(self, xleft, xright):
        xmin, xmax = self.fig.axes[0].get_xlim()
        if xleft < xmin:
            xleft = xmin
        if xright > xmax:
            xright = xmax
        if xleft < self.xmin:
            xleft = self.xmin
        if xright > self.xmax:
            xright = self.xmax
        self.xleft, self.xright = xleft, xright
        for s in self.selectors:
            s.xy[:2, 0] = self.xleft
            s.xy[2:4, 0] = self.xright
        self.valueChanged.emit(self.xleft, self.xright)
        self.fig.canvas.draw_idle()

    def get_selector_limits(self):
        return self.xleft, self.xright

    def set_selection_limits(self, xmin, xmax):
        self.xmin, self.xmax = xmin, xmax

    def get_selection_limits(self):
        return self.xmin, self.xmax

    def set_active(self, value):
        """"""
        if value != self.active:
            self.active = value
            self.toogled.emit(value)
            for s in self.selectors:
                s.set_visible(value)


class EventMarker(QtCore.QObject):
    """
    """

    valueChanged = QtCore.Signal(float)

    def __init__(self, fig, event):
        super(EventMarker, self).__init__()
        self.fig = fig
        self.event = event

        self.markers = []

        for ax in fig.axes:
            marker = ax.axvline(self.event.time)
            marker.set(color='r', ls='--', lw=2, alpha=0.8, picker=5)
            self.markers.append(marker)


class ThresholdMarker(QtCore.QObject):
    """
    """

    thresholdChanged = QtCore.Signal(float)

    def __init__(self, ax, threshold=0.0):
        super(ThresholdMarker, self).__init__()
        self.ax = ax
        self.threshold = threshold
        self.active = False

        # Set threshold line
        self.figThreshold = self.ax.axhline(self.threshold)
        self.figThreshold.set(color='b', ls='--', lw=2, alpha=0.8, picker=5)

        # Set threshold label
        bbox = dict(boxstyle="round", fc="Lightblue", ec="b", alpha=0.8)
        self.figThresholdLabel = self.ax.text(0, 0, "0.00", bbox=bbox)
        self.figThresholdLabel.set_visible(False)
        self.pick_threshold = None

        self.canvas = self.ax.figure.canvas
        self.canvas.mpl_connect('pick_event', self.onpick)
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('motion_notify_event', self.onmove)

    def onpick(self, event):
        if event.artist == self.figThreshold:
            if self.active and not self.canvas.widgetlock.locked():
                self.canvas.widgetlock(self)
                self.pick_threshold = event
                xdata, ydata = self.get_data(event.mouseevent)
                # Draw legend
                self.figThresholdLabel.set_position((xdata, ydata))
                self.figThresholdLabel.set_visible(True)
                self.canvas.draw_idle()

    def onrelease(self, event):
        if self.canvas.widgetlock.isowner(self):
            self.figThresholdLabel.set_visible(False)
            self.pick_threshold = None
            self.canvas.draw_idle()
            self.canvas.widgetlock.release(self)

    def onmove(self, event):
        if self.pick_threshold is not None:
            xdata, ydata = self.get_data(event)
            self.set_threshold(round(ydata, 2))
            # Draw legend
            self.figThresholdLabel.set_position((xdata, ydata))
            self.canvas.draw_idle()

    def get_data(self, event):
        inv = self.ax.transData.inverted()
        xdata, ydata = inv.transform((event.x, event.y))
        ymin, ymax = self.ax.get_ylim()
        xmin, xmax = self.ax.get_xlim()
        if ydata < ymin:
            ydata = ymin
        elif ydata > ymax:
            ydata = ymax
        if ydata < 0.0:
            ydata = 0.0
        if xdata < xmin:
            xdata = xmin
        elif xdata > xmax:
            xdata = xmax
        return xdata, ydata

    def set_threshold(self, value):
        if value >= 0:
            self.threshold = value
            self.thresholdChanged.emit(self.threshold)
            self.figThreshold.set_ydata(self.threshold)
            self.figThresholdLabel.set_text("Threshold: %.2f" % self.threshold)
            if self.figThreshold.get_visible():
                self.canvas.draw_idle()

    def set_visible(self, value):
        self.figThreshold.set_visible(value)
        self.active = value
        self.canvas.draw_idle()


class MiniMap(QtGui.QWidget):
    """
    """

    def __init__(self, parent, ax, record=None):
        super(MiniMap, self).__init__(parent)
        self.ax = ax

        self.xmin = 0.0
        self.xmax = 0.0
        self.step = 10.0
        self.time = np.array([])

        self.minimapFig = plt.figure()
        self.minimapFig.set_figheight(0.75)
        self.minimapFig.add_axes((0, 0, 1, 1))
        self.minimapCanvas = FigureCanvas(self.minimapFig)
        self.minimapCanvas.setMinimumSize(self.minimapCanvas.size())
        self.minimapSelector = self.minimapFig.axes[0].axvspan(0, self.step,
                                                               color='gray',
                                                               alpha=0.5,
                                                               animated=True)
        self.minimapSelection = self.minimapFig.axes[0].axvspan(0, self.step,
                                                                color = 'LightCoral',
                                                                alpha = 0.5,
                                                                animated=True)
        self.minimapSelection.set_visible(False)
        self.minimapBackground = []
        self.minimapSize = (self.minimapFig.bbox.width,
                            self.minimapFig.bbox.height)

        self.press_selector = None
        self.minimapCanvas.mpl_connect('button_press_event', self.onpress)
        self.minimapCanvas.mpl_connect('button_release_event', self.onrelease)
        self.minimapCanvas.mpl_connect('motion_notify_event', self.onmove)

        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.minimapCanvas)

        self.record = None
        if record is not None:
            self.set_record(record)

    def set_record(self, record, step):
        """"""
        self.record = record
        self.step = step
        self.time = np.arange(len(self.record.signal)) / self.record.fs
        self.xmin = self.time[0]
        self.xmax = self.time[-1]

        ax = self.minimapFig.axes[0]
        ax.lines = []
        formatter = FuncFormatter(lambda x, pos: str(datetime.timedelta(seconds=x)))
        ax.xaxis.set_major_formatter(formatter)
        ax.grid(True, which='both')
        ax.plot(self.time, self.record.signal, color='black', rasterized=True)
        ax.set_xlim(self.xmin, self.xmax)
        # Draw canvas
        self.minimapCanvas.draw()
        self.minimapBackground = self.minimapCanvas.copy_from_bbox(self.minimapFig.bbox)
        self.draw_animate()

    def onpress(self, event):
        self.press_selector = event
        xdata = round(self.get_xdata(event), 3)
        xmin = round(xdata - (self.step / 2.0), 3)
        xmax = round(xdata + (self.step / 2.0), 3)
        self.set_selector_limits(xmin, xmax)

    def onrelease(self, event):
        self.press_selector = None

    def onmove(self, event):
        if self.press_selector is not None:
            xdata = round(self.get_xdata(event), 3)
            xmin = round(xdata - (self.step / 2.0), 3)
            xmax = round(xdata + (self.step / 2.0), 3)
            self.set_selector_limits(xmin, xmax)

    def get_xdata(self, event):
        inv = self.minimapFig.axes[0].transData.inverted()
        xdata, _ = inv.transform((event.x, event.y))
        return xdata

    def set_selector_limits(self, xmin, xmax):
        self.step = xmax - xmin
        if self.step >= self.xmax - self.xmin:
            xleft = self.xmin
            xright = self.xmax
        if xmin < self.xmin:
            xleft = self.xmin
            xright = self.step
        elif xmax > self.xmax:
            xleft = self.xmax - self.step
            xright = self.xmax
        else:
            xleft = xmin
            xright = xmax
        self.minimapSelector.xy[:2, 0] = xleft
        self.minimapSelector.xy[2:4, 0] = xright
        self.ax.set_xlim(xleft, xright)

    def get_selector_limits(self):
        return self.minimapSelector.xy[0, 0], self.minimapSelector.xy[2, 0]

    def draw_animate(self):
        size = self.minimapFig.bbox.width, self.minimapFig.bbox.height
        if size != self.minimapSize:
            self.minimapSize = size
            self.minimapCanvas.draw()
            self.minimapBackground = self.minimapCanvas.copy_from_bbox(self.minimapFig.bbox)
        self.minimapCanvas.restore_region(self.minimapBackground)
        self.minimapFig.draw_artist(self.minimapSelection)
        self.minimapFig.draw_artist(self.minimapSelector)
        self.minimapCanvas.blit(self.minimapFig.bbox)

    def set_visible(self, value):
        self.minimapCanvas.setVisible(value)

    def set_selection_limits(self, xleft, xright):
        self.minimapSelection.xy[:2, 0] = xleft
        self.minimapSelection.xy[2:4, 0] = xright
        self.draw_animate()

    def set_selection_visible(self, value):
        self.minimapSelection.set_visible(value)
        self.draw_animate()


class SignalViewerWidget(QtGui.QWidget):
    """
    """

    def __init__(self, parent, record=None):
        super(SignalViewerWidget, self).__init__(parent)

        self.xmin = 0.0
        self.xmax = 0.0
        self.scale = 1e3  # Conversion between scrolling and axis units
        self.time = np.array([])

        self._signal_data = None
        self._envelope_data = None

        self.fig, _ = plt.subplots(3, 1, sharex=True)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumSize(self.canvas.size())
        self.graphArea = QtGui.QScrollArea(self)
        self.graphArea.setWidgetResizable(True)
        self.graphArea.setWidget(self.canvas)
        self.toolbar = QtGui.QToolBar(self)

        self.eventMarkers = []
        self.thresholdMarker = None
        self.selector = SpanSelector(self.fig)
        self.minimap = MiniMap(self, self.fig.axes[0], record)

        self.spinbox = QtGui.QTimeEdit(QtCore.QTime.currentTime(),
                                       parent=self.toolbar)
        self.toolbar.addWidget(self.spinbox)
        self.toolbar.setVisible(False)

        for ax in self.fig.axes:
            ax.callbacks.connect('xlim_changed', self.on_xlim_change)

        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.graphArea)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.minimap)

        self.selector.toogled.connect(self.minimap.set_selection_visible)
        self.selector.valueChanged.connect(self.minimap.set_selection_limits)

        self.record = None
        if record is not None:
            self.set_record(record)

    def set_record(self, record, step=20.0):
        """"""
        self.record = record
        self.time = np.arange(len(self.record.signal)) / self.record.fs
        self.xmax = self.time[-1]
        # Draw minimap
        self.minimap.set_record(record, step)
        # Plot signal
        #self.fig.axes[0].cla()
        formatter = FuncFormatter(lambda x, pos: str(datetime.timedelta(seconds=x)))
        self.fig.axes[0].xaxis.set_major_formatter(formatter)
        self.fig.axes[0].grid(True, which='both')
        self.fig.axes[0].lines = []
        self._signal_data = self.fig.axes[0].plot(self.time,
                                                  self.record.signal,
                                                  color='black',
                                                  rasterized=True)[0]
        # Plot envelope
        self._envelope_data = self.fig.axes[0].plot(self.time,
                                                    env.envelope(self.record.signal),
                                                    color='red',
                                                    rasterized=True)[0]
        # Plot CF
        self.set_cf_visible(self.record.cf.size != 0)
        self.fig.axes[1].cla()
        self.fig.axes[1].xaxis.set_major_formatter(formatter)
        self.fig.axes[1].grid(True, which='both')
        self.fig.axes[1].lines = []
        self.fig.axes[1].plot(self.time[:len(self.record.cf)], self.record.cf,
                              color='black', rasterized=True)
        self.thresholdMarker = ThresholdMarker(self.fig.axes[1])
        # Plot espectrogram
        self.fig.axes[2].cla()
        self.fig.axes[2].xaxis.set_major_formatter(formatter)
        self.fig.axes[2].specgram(self.record.signal, Fs=self.record.fs,
                                  cmap='jet',
                                  xextent=(self.xmin, self.xmax),
                                  rasterized=True)
        # Plot events
        self.eventMarkers = []
        for event in self.record.events:
            self.eventMarkers.append(EventMarker(self.fig, event))
        # Set the span selector
        self.selector.set_active(False)
        self.selector.set_selection_limits(self.xmin, self.xmax)
        # Set the initial xlimits
        self.set_xlim(0, step)
        # Adjust the space between subplots
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05,
                                 top=0.95, hspace=0.1)

    def set_xlim(self, l, r):
        xmin = max(0, l)
        xmax = min(self.xmax, r)
        self.fig.axes[0].set_xlim(xmin, xmax)

    def on_xlim_change(self, ax):
        xmin, xmax = ax.get_xlim()
        # Update minimap selector
        if (xmin, xmax) != self.minimap.get_selector_limits():
            self.minimap.set_selector_limits(xmin, xmax)
        self.draw_idle()

    def set_position(self, pos):
        """"""
        xmin, xmax = self.fig.axes[0].get_xlim()
        mrange = xmax - xmin
        l, r = pos - mrange / 2.0, pos + mrange / 2.0
        if l < self.xmin:
            l, r = self.xmin, mrange
        elif r > self.xmax:
            l, r = self.xmax - mrange, self.xmax
        self.set_xlim(l, r)

    def draw_idle(self):
        self.canvas.draw_idle()
        self.minimap.draw_animate()

    def set_signal_amplitude_visible(self, show_sa):
        """"""
        if self._signal_data is not None and self._envelope_data is not None:
            self._signal_data.set_visible(show_sa)
            show_axis = (self._signal_data.get_visible() +
                         self._envelope_data.get_visible())
            self.fig.axes[0].set_visible(show_axis)
            self.subplots_adjust()
            self.draw_idle()

    def set_signal_envelope_visible(self, show_se):
        """"""
        if self._signal_data is not None and self._envelope_data is not None:
            self._envelope_data.set_visible(show_se)
            show_axis = (self._signal_data.get_visible() +
                         self._envelope_data.get_visible())
            self.fig.axes[0].set_visible(show_axis)
            self.subplots_adjust()
            self.draw_idle()

    def set_cf_visible(self, show_cf):
        """"""
        self.fig.axes[1].set_visible(show_cf)
        self.subplots_adjust()
        self.draw_idle()

    def set_espectrogram_visible(self, show_eg):
        """"""
        self.fig.axes[2].set_visible(show_eg)
        self.subplots_adjust()
        self.draw_idle()

    def set_minimap_visible(self, show_mm):
        """"""
        self.minimap.set_visible(show_mm)
        self.draw_idle()

    def set_threshold_visible(self, show_thr):
        """"""
        self.thresholdMarker.set_visible(show_thr)
        self.canvas.draw_idle()

    def subplots_adjust(self):
        """"""
        visible_subplots = [ax for ax in self.fig.get_axes() if ax.get_visible()]
        for i, ax in enumerate(visible_subplots):
            ax.change_geometry(len(visible_subplots), 1, i + 1)

    def get_selector_limits(self):
        self.selector.get_selector_limits()

    def set_selector_limits(self, xleft, xright):
        self.selector.set_selector_limits(xleft, xright)


class LoadDialog(QtGui.QDialog, ui_loaddialog.Ui_LoadDialog):
    """
    """

    def __init__(self, parent, filename):
        super(LoadDialog, self).__init__(parent)
        self.setupUi(self)
        self.filename = filename
        self.formats = ['binary', 'text']
        self.dtypes = ['float16', 'float32', 'float64']
        self.byteorders = ['little-endian', 'big-endian']

        self.FileFormatComboBox.currentIndexChanged.connect(self.on_format_change)
        self.FileFormatComboBox.currentIndexChanged.connect(self.load_preview)
        self.DataTypeComboBox.currentIndexChanged.connect(self.load_preview)
        self.ByteOrderComboBox.currentIndexChanged.connect(self.load_preview)

        # Set Defaults
        if futils.istextfile(self.filename):
            self.FileFormatComboBox.setCurrentIndex(1)
        else:
            self.FileFormatComboBox.setCurrentIndex(0)
        if futils.is_little_endian():
            self.ByteOrderComboBox.setCurrentIndex(0)
        else:
            self.ByteOrderComboBox.setCurrentIndex(1)

        self.load_preview()

    def on_format_change(self, idx):
        """"""
        fmt = self.formats[self.FileFormatComboBox.currentIndex()]
        if fmt == 'binary':
            self.DataTypeComboBox.setVisible(True)
            self.DataTypeLabel.setVisible(True)
            self.ByteOrderComboBox.setVisible(True)
            self.ByteOrderLabel.setVisible(True)
        elif fmt == 'text':
            self.DataTypeComboBox.setVisible(False)
            self.DataTypeLabel.setVisible(False)
            self.ByteOrderComboBox.setVisible(False)
            self.ByteOrderLabel.setVisible(False)

    def load_preview(self):
        """"""
        # Load parameters
        values = self.get_values()
        # Set up a file handler according to the type of raw data (binary or text)
        fhandler = rawfile.get_file_handler(self.filename, **values)
        # Print data preview
        array = fhandler.read_in_blocks().next()
        data = ''
        for x in array:
            data += ("%s\n" % x)
        self.PreviewTextEdit.clear()
        self.PreviewTextEdit.setText(data)

    def get_values(self):
        """"""
        return {'fmt': self.formats[self.FileFormatComboBox.currentIndex()],
                'dtype': self.dtypes[self.DataTypeComboBox.currentIndex()],
                'byteorder': self.byteorders[self.ByteOrderComboBox.currentIndex()],
                'fs': float(self.SampleFrequencySpinBox.value())}


class FilterListModel(QtCore.QAbstractTableModel):
    """
    """

    sizeChanged = QtCore.Signal(int)

    def __init__(self, listobj, header=None):
        QtCore.QAbstractTableModel.__init__(self)
        self._list = listobj
        if header is None:
            header = ['Length (in seconds)']
        self._header = header

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return "%s" % self._list[index.row()]

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._header[section]
        return None

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self._list.sort(reverse=(order == QtCore.Qt.DescendingOrder))
        self.layoutChanged.emit()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            self._list[index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return (QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsEnabled)

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        if row < 0 or row > len(self._list):
            return
        self.beginRemoveRows(parent, row, row + count - 1)
        while count != 0:
            del self._list[row]
            count -= 1
        self.sizeChanged.emit(len(self._list))
        self.endRemoveRows()

    def addFilter(self, value=10.0):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._list),
                             len(self._list))
        self._list.append(value)
        self.sizeChanged.emit(len(self._list))
        self.endInsertRows()

    def list(self):
        return self._list


class SettingsDialog(QtGui.QDialog, ui_settingsdialog.Ui_SettingsDialog):
    """
    """

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)

        self._filters = FilterListModel([])
        self.filtersTable.setModel(self._filters)
        self._filters.sizeChanged.connect(self._onSizeChanged)
        filterDelegate = DoubleSpinBoxDelegate(self.filtersTable)
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
        """"""
        self.settings = QtCore.QSettings(_organization, _application_name)
        self.settings.beginGroup("stalta_settings")
        self.staSpinBox.setValue(float(self.settings.value('sta_window_len', 5.0)))
        self.ltaSpinBox.setValue(float(self.settings.value('lta_window_len', 100.0)))
        self.settings.endGroup()
        self.settings.beginGroup("ampa_settings")
        self.ampawindowSpinBox.setValue(float(self.settings.value('window_len', 100.0)))
        self.ampawindowoverlapSpinBox.setValue(float(self.settings.value('overlap', 0.5)))
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

    def saveSettings(self):
        """"""
        self.settings = QtCore.QSettings(_organization, _application_name)
        self.settings.beginGroup("stalta_settings")
        self.settings.setValue('sta_window_len', self.staSpinBox.value())
        self.settings.setValue('lta_window_len', self.ltaSpinBox.value())
        self.settings.endGroup()
        self.settings.beginGroup("ampa_settings")
        self.settings.setValue('window_len', self.ampawindowSpinBox.value())
        self.settings.setValue('overlap', self.ampawindowoverlapSpinBox.value())
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


class PickingTask(QtCore.QObject):
    """"""

    finished = QtCore.Signal()

    def __init__(self, record, alg, threshold=None):
        super(PickingTask, self).__init__()
        self.record = record
        self.alg = alg
        self.threshold = threshold

    def run(self):
        """"""
        settings = QtCore.QSettings(_organization, _application_name)
        takanami = int(settings.value('takanami_settings/takanami', False))
        takanami_margin = float(settings.value('takanami_margin', 5.0))
        self.record.detect(self.alg, threshold=self.threshold,
                           takanami=takanami,
                           takanami_margin=takanami_margin)
        self.finished.emit()


class PickingTaskDialog(QtGui.QDialog):
    """
    """

    def __init__(self, record, alg, threshold=None):
        QtGui.QDialog.__init__(self)
        self.record = record
        self._events = self.record.events
        self.alg = alg
        self.threshold = threshold
        self.init_ui()

        self._thread = QtCore.QThread(self)
        self._task = PickingTask(self.record, self.alg, self.threshold)
        self._task.moveToThread(self._thread)
        self._thread.started.connect(self._task.run)
        self._task.finished.connect(self._thread.quit)
        self._task.finished.connect(self.accept)
        self._task.finished.connect(self._task.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def init_ui(self):
        self.setWindowTitle('Signal processing')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.label = QtGui.QLabel("Applying %s..." % self.alg._name, self)
        self.pbarWidget = QtGui.QWidget(self)
        self.pbar = QtGui.QProgressBar(self.pbarWidget)
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(0)
        #self.button_cancel = QtGui.QPushButton('&Cancel', self.pbarWidget)
        self.hlayout = QtGui.QHBoxLayout(self.pbarWidget)
        self.hlayout.addWidget(self.pbar)
        #self.hlayout.addWidget(self.button_cancel)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.pbarWidget)
        #self.button_cancel.clicked.connect(self.reject)

    def reject(self):
        self._thread.terminate()
        self._thread.wait()
        self.record.events = self._events
        return QtGui.QDialog.reject(self)


class MainWindow(QtGui.QMainWindow, ui_mainwindow.Ui_MainWindow):
    """"""

    windowList = []
    MaxRecentFiles = 10

    def __init__(self, parent=None, filename=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.record = None
        self._model = None
        self.isModified = False
        self.saved_filename = None
        self.picking_task = None

        stateDelegate = ComboBoxDelegate(self.EventsTableView, rc.Event.states)
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

        self.signalViewer = SignalViewerWidget(self.splitter)
        self.splitter.addWidget(self.signalViewer)
        self.toolBarNavigation = NavigationToolbar(self.signalViewer.canvas,
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
        """"""
        if filename is None:
            filename, _ = QtGui.QFileDialog.getOpenFileName(self, "Open Data File", ".",
                                                            "Binary Files (*.bin *.raw);;Text Files (*.txt);;All Files (*.*)")
        if filename != '':
            if self.record is None:
                dialog = LoadDialog(self, filename)
                return_code = dialog.exec_()
                if return_code == QtGui.QDialog.Accepted:
                    values = dialog.get_values()
                    # Load and visualize the opened record
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                    self.record = rc.Record(filename, **values)
                    self._model = EventListModel(self.record, ['name', 'time',
                                                               'cf_value',
                                                               'mode',
                                                               'method',
                                                               'state',
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
        """"""
        action = self.sender()
        if action:
            self.open(action.data())

    def save(self):
        """"""
        if self.saved_filename is None:
            return self.save_as()
        else:
            return self.save_events(self.saved_filename)

    def save_as(self):
        """"""
        filename, _ = QtGui.QFileDialog.getSaveFileName(self, "Open Data File", ".",
                                                        "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)")
        if filename != '':
            self.save_events(filename)

    def save_events(self, filename):
        """"""
        with open(filename, 'w') as f:
            rc.generate_csv([self.record], f)
            self.saved_filename = filename

    def close(self):
        """"""
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
        """"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def push_recent_list(self, filename):
        """"""
        settings = QtCore.QSettings(_organization, _application_name)
        files = self.get_recent_list()
        if filename in files:
            files.remove(filename)
        files.insert(0, filename)
        settings.setValue('recentFileList', files)
        self.set_recent_menu()

    def get_recent_list(self):
        """"""
        settings = QtCore.QSettings(_organization, _application_name)
        files = settings.value('recentFileList')
        if files:
            if isinstance(files, list):
                return list(files)
            else:
                return [files]
        return []

    def clear_recent_list(self):
        """"""
        settings = QtCore.QSettings(_organization, _application_name)
        settings.setValue('recentFileList', [])
        self.set_recent_menu()

    def set_recent_menu(self):
        """"""
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

    def on_close(self):
        """"""
        self.centralwidget.setVisible(False)
        self.actionClose.setEnabled(False)
        self.actionSelect_All.setEnabled(False)
        self.actionCreate_New_Event.setEnabled(False)
        self.actionSTA_LTA.setEnabled(False)
        self.actionAMPA.setEnabled(False)
        self.actionPlay.setEnabled(False)
        self.toolBarNavigation.setEnabled(False)
        self.set_title()

    def maybeSave(self):
        """"""
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
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def set_modified(self, value):
        """"""
        self.isModified = value
        self.actionSave.setEnabled(value)
        self.actionSave_As.setEnabled(value)
        self.actionGenerate_HTML.setEnabled(value)

    def set_title(self):
        prefix = '' if self.record is None else "%s - " % self.record.filename
        self.setWindowTitle('%sP-phase Picker v.%s' % (prefix, __version__))

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

    def toogle_threshold(self, value):
        self.thresholdLabel.setEnabled(value)
        self.thresholdSpinBox.setEnabled(value)
        self.signalViewer.thresholdMarker.set_visible(value)

    def onPickingFinished(self):
        """"""
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
        """"""
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
        return_code = PickingTaskDialog(self.record, alg, threshold).exec_()
        if return_code == QtGui.QDialog.Accepted:
            self.onPickingFinished()

    def doAMPA(self):
        """"""
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
        return_code = PickingTaskDialog(self.record, alg, threshold).exec_()
        if return_code == QtGui.QDialog.Accepted:
            self.onPickingFinished()

    def goToEventPosition(self, index):
        """"""
        self.signalViewer.set_position(self.record.events[index.row()].time)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

































