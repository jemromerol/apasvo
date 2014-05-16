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

import matplotlib
matplotlib.rcParams['backend'] = 'qt4agg'
matplotlib.rcParams['backend.qt4'] = 'PySide'
matplotlib.rcParams['patch.antialiased'] = False
matplotlib.rcParams['figure.dpi'] = 65
matplotlib.rcParams['agg.path.chunksize'] = 80000
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np
import datetime

from apasvo.gui.views import takanamidialog
from apasvo.gui.views import settingsdialog
from apasvo.picking import envelope as env
from apasvo.picking import record as rc
from apasvo.utils import plotting
from apasvo.utils import clt

from apasvo._version import _application_name
from apasvo._version import _organization


class SpanSelector(QtCore.QObject):
    """Allows the user to manually select a piece of a seismic signal on a
    SignalViewerWidget object.

    Attributes:
        xleft: Current selection lower limit (measured in h-axis units).
        xright: Current selection upper limit (measured in h-axis units).
        xmin: Minimum selection lower limit allowed (in h-axis units).
        xmax: Maximum selection upper limit allowed (in h-axis units).
        active: Indicates whether the selector object is active or not.
        minstep: Minimun selection step allowed.

    Signals:
        toogled: 'active' state changes.
        valueChanged: 'xleft', 'xright' values changes.
    """

    toggled = QtCore.Signal(bool)
    valueChanged = QtCore.Signal(float, float)
    right_clicked = QtCore.Signal()

    def __init__(self, fig, fs=50.0, xmin=0.0, xmax=0.0):
        super(SpanSelector, self).__init__()
        self.fig = fig
        self._xleft_in_samples = 0
        self._xright_in_samples = 0
        self.fs = fs
        self._xmin_in_samples = int(xmin * self.fs)
        self._xmax_in_samples = int(xmax * self.fs)
        self.active = False
        self.enabled = True

        self.selectors = [ax.axvspan(0, 1, fc='LightCoral', ec='r', alpha=0.5, picker=5)
                          for ax in self.fig.axes]
        for s in self.selectors:
            s.set_visible(False)

        self.pick_threshold = None

        self.press_selector = None
        self.canvas = self.fig.canvas
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('button_press_event', self.onpress)
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('motion_notify_event', self.onmove)

        self.background = None
        self.animated = False

    @property
    def xleft(self):
        return self._xleft_in_samples / self.fs

    @property
    def xright(self):
        return self._xright_in_samples / self.fs

    @property
    def xmin(self):
        return self._xmin_in_samples / self.fs

    @property
    def xmax(self):
        return self._xmax_in_samples / self.fs

    @xmin.setter
    def xmin(self, value):
        self._xmin_in_samples = int(value * self.fs)

    @xmax.setter
    def xmax(self, value):
        self._xmax_in_samples = int(value * self.fs)

    def on_pick(self, pick_event):
        if self.active:
            if pick_event.mouseevent.button == 3:  # Right button clicked
                if pick_event.artist in self.selectors:
                    if not self.canvas.widgetlock.locked():
                        self.right_clicked.emit()

    def onpress(self, event):
        if self.enabled:
            if event.button == 1:  # Left button clicked
                if not self.canvas.widgetlock.locked():
                    self.canvas.widgetlock(self)
                    if self.active:
                        self.set_active(False)
                    self.press_selector = event
                    # Start animation
                    self._set_animated(True)
                    xpos = self.get_xdata(self.press_selector)
                    self.set_selector_limits(xpos, xpos, adjust_to_viewport=True)

    def onrelease(self, event):
        if self.canvas.widgetlock.isowner(self):
            self.press_selector = None
            # End animation
            self._set_animated(False)
            self.canvas.widgetlock.release(self)

    def onmove(self, event):
        if self.press_selector is not None:
            xleft = self.get_xdata(self.press_selector)
            xright = self.get_xdata(event)
            if xright < xleft:
                xleft, xright = xright, xleft
            if not self.active:
                self.set_active(True)
            self.set_selector_limits(xleft, xright, adjust_to_viewport=True)

    def get_xdata(self, event):
        inv = self.fig.axes[0].transData.inverted()
        xdata, _ = inv.transform((event.x, event.y))
        return xdata

    def set_selector_limits(self, xleft, xright, adjust_to_viewport=False):
        xleft = int(xleft * self.fs)
        xright = int(xright * self.fs)
        if (xleft, xright) != (self._xleft_in_samples, self._xright_in_samples):
            if adjust_to_viewport:
                xmin, xmax = self.fig.axes[0].get_xlim()
                xmin, xmax = int(xmin * self.fs), int(xmax * self.fs)
                if xleft < xmin:
                    xleft = xmin
                elif xleft > xmax:
                    xleft = xmax
                if xright > xmax:
                    xright = xmax
                elif xright < xmin:
                    xright = xmin
                if xleft < self._xmin_in_samples:
                    xleft = self._xmin_in_samples
                if xright > self._xmax_in_samples:
                    xright = self._xmax_in_samples
            self._xleft_in_samples, self._xright_in_samples = xleft, xright
            for s in self.selectors:
                s.xy[:2, 0] = self.xleft
                s.xy[2:4, 0] = self.xright
            self.valueChanged.emit(self.xleft, self.xright)
            self.draw()

    def get_selector_limits(self):
        return self.xleft, self.xright

    def set_selection_limits(self, xmin, xmax):
        self.xmin, self.xmax = xmin, xmax

    def get_selection_limits(self):
        return self.xmin, self.xmax

    def set_active(self, value):
        if value != self.active:
            self.active = value
            self.toggled.emit(value)
            for s in self.selectors:
                s.set_visible(value)
            self.draw()

    def set_enabled(self, value):
        if value != self.enabled:
            self.enabled = value
            for s in self.selectors:
                if value == True:
                    s.set_edgecolor('Red')
                    s.set_facecolor('LightCoral')
                else:
                    s.set_edgecolor('DarkSlateGray')
                    s.set_facecolor('Gray')

    def draw(self):
        if self.animated:
            self._draw_animate()
        else:
            self.canvas.draw_idle()

    def _draw_animate(self):
        self.canvas.restore_region(self.background)
        if self.active:
            for s in self.selectors:
                if s.get_axes().get_visible():
                    self.fig.draw_artist(s)
            self.canvas.blit(self.fig.bbox)

    def _set_animated(self, value):
        if self.animated != value:
            self.animated = value
            for s in self.selectors:
                s.set_animated(value)
            if self.animated == True:
                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.fig.bbox)


class EventMarker(QtCore.QObject):
    """Plots a vertical line marker to indicate the arrival time of
    a detected event on a SignalViewerWidget object.

    Attributes:
        event: Marked event.

    Signals:
        valueChanged: 'event' arrival time changed.
    """

    event_selected = QtCore.Signal(rc.Event)
    right_clicked = QtCore.Signal(rc.Event)

    def __init__(self, fig, minimap, document, event, color='b', selected_color='r'):
        super(EventMarker, self).__init__()
        self.fig = fig
        self.minimap = minimap
        self.event = event
        self.document = document
        self.position = self.event.time

        self.selected = False
        self.color = color
        self.selected_color = selected_color

        self.markers = []
        # draw markers
        pos = self.event.time / self.event.record.fs
        for ax in self.fig.axes:
            marker = ax.axvline(pos)
            marker.set(color=self.color, ls='--', lw=2, picker=5)
            self.markers.append(marker)
        # draw minimap marker
        self.minimap.create_marker(event, pos, color=self.color, ls='-', lw=1)
        # draw label
        bbox = dict(boxstyle="round", fc="LightCoral", ec="r", alpha=0.8)
        self.position_label = self.fig.text(0, 0,
                                            "Time: 00:00:00.000 seconds\nCF value: 0.000",
                                            bbox=bbox)
        self.position_label.set_visible(False)

        self.canvas = self.fig.canvas
        self.canvas.mpl_connect('pick_event', self.onpick)
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('motion_notify_event', self.onmove)
        self.pick_event = None

        # Animation related attrs.
        self.background = None
        self.animated = False

        self.draw()

    def onpick(self, pick_event):
        if pick_event.artist in self.markers:
            if not self.canvas.widgetlock.locked():
                if pick_event.mouseevent.button == 1:  # left button clicked
                    self.canvas.widgetlock(self)
                    self.pick_event = pick_event
                    xfig, yfig = self._event_to_fig_coords(pick_event.mouseevent)
                    self.position_label.set_position((xfig, yfig))
                    self.event_selected.emit(self.event)
                    self.draw()

                elif pick_event.mouseevent.button == 3:  # Right button clicked
                    self.event_selected.emit(self.event)
                    self.draw()
                    self.right_clicked.emit(self.event)

    def onrelease(self, mouse_event):
        if self.canvas.widgetlock.isowner(self):
            self.position_label.set_visible(False)
            self.pick_event = None
            # End animation
            self.draw()
            self._set_animated(False)

            self.canvas.widgetlock.release(self)
            if self.position != self.event.time:
                self.document.editEvent(self.event, time=self.position,
                                        mode=rc.mode_manual,
                                        method=rc.method_other)

    def onmove(self, mouse_event):
        if self.pick_event is not None:
            xdata = self.get_xdata(mouse_event)
            self.set_position(xdata)
            xfig, yfig = self._event_to_fig_coords(mouse_event)
            self.position_label.set_position((xfig, yfig))
            self.position_label.set_visible(True)
            self._set_animated(True)
            self.draw()

    def get_xdata(self, event):
        inv = self.fig.axes[0].transData.inverted()
        xdata, _ = inv.transform((event.x, event.y))
        return xdata

    def _event_to_fig_coords(self, event):
        inv = self.fig.transFigure.inverted()
        return inv.transform((event.x, event.y))

    def set_position(self, value):
        time_in_samples = int(value * self.event.record.fs)
        if time_in_samples != self.position:
            if 0 <= time_in_samples <= len(self.event.record.signal):
                self.position = time_in_samples
                time_in_seconds = time_in_samples / float(self.event.record.fs)
                for marker in self.markers:
                    marker.set_xdata(time_in_seconds)
                if 0 <= self.position < len(self.event.record.cf):
                    cf_value = self.event.record.cf[self.position]
                else:
                    cf_value = np.nan
                self.position_label.set_text("Time: %s seconds.\nCF value: %.6g" %
                                             (clt.float_secs_2_string_date(time_in_seconds), cf_value))
                self.minimap.set_marker_position(self.event, time_in_seconds)

    def remove(self):
        for ax, marker in zip(self.fig.axes, self.markers):
            ax.lines.remove(marker)
        self.minimap.delete_marker(self.event)
        self.draw()

    def set_selected(self, value):
        if self.selected != value:
            self.selected = value
            color = self.selected_color if self.selected else self.color
            for marker in self.markers:
                marker.set(color=color)
            self.minimap.set_marker(self.event, color=color)

    def update(self):
        if self.event.time != self.position:
            self.set_position(self.event.time / float(self.event.record.fs))
            self.draw()

    def draw(self):
        if self.animated:
            self._draw_animate()
        else:
            self.canvas.draw_idle()
        self.minimap.draw()

    def _draw_animate(self):
        self.canvas.restore_region(self.background)
        for marker in self.markers:
            if marker.get_axes().get_visible() and marker.get_visible():
                self.fig.draw_artist(marker)
        if self.position_label.get_visible():
            self.fig.draw_artist(self.position_label)
        self.canvas.blit(self.fig.bbox)

    def _set_animated(self, value):
        if self.animated != value:
            self.animated = value
            for marker in self.markers:
                marker.set_animated(value)
            self.position_label.set_animated(value)
            if self.animated == True:
                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.fig.bbox)


class ThresholdMarker(QtCore.QObject):
    """Plots an horizontal line marker on a SignalViewerWidget to
    indicate a selected threshold value for the computed
    characteristic function.

    Attributes:
        threshold: A threshold value. Default: 0.0.
        active: Indicates whether the marker is active or not.

    Signals:
        thresholdChanged: 'threshold' value changed.
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
        self.figThreshold.set_visible(False)

        # Set threshold label
        bbox = dict(boxstyle="round", fc="Lightblue", ec="b", alpha=0.8)
        self.figThresholdLabel = self.ax.text(0, 0, "0.00", bbox=bbox)
        self.figThresholdLabel.set_visible(False)
        self.pick_threshold = None

        self.canvas = self.ax.figure.canvas
        self.canvas.mpl_connect('pick_event', self.onpick)
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('motion_notify_event', self.onmove)

        # Animation related attrs.
        self.background = None
        self.animated = False

    def onpick(self, event):
        if self.active:
            if event.mouseevent.button == 1:  # left button clicked
                if event.artist == self.figThreshold:
                    if not self.canvas.widgetlock.locked():
                        self.canvas.widgetlock(self)
                        self.pick_threshold = event
                        xdata, ydata = self.get_data(event.mouseevent)
                        # Draw legend
                        self.figThresholdLabel.set_position((xdata, ydata))
                        self.figThresholdLabel.set_visible(True)
                        self.draw()

    def onrelease(self, event):
        if self.canvas.widgetlock.isowner(self):
            self.figThresholdLabel.set_visible(False)
            self.pick_threshold = None
            # End animation
            self._set_animated(False)
            self.draw()

            self.canvas.widgetlock.release(self)

    def onmove(self, event):
        if self.pick_threshold is not None:
            xdata, ydata = self.get_data(event)
            self.set_threshold(round(ydata, 2))
            # Draw legend
            self.figThresholdLabel.set_position((xdata, ydata))
            self._set_animated(True)
            self.draw()

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
        if self.threshold != value:
            if value >= 0:
                self.threshold = value
                self.thresholdChanged.emit(self.threshold)
                self.figThreshold.set_ydata(self.threshold)
                self.figThresholdLabel.set_text("Threshold: %.2f" % self.threshold)
                self.draw()

    def set_visible(self, value):
        if self.active != value:
            self.figThreshold.set_visible(value)
            self.active = value
            self.draw()

    def get_visible(self):
        return self.active

    def draw(self):
        if self.animated:
            self._draw_animate()
        else:
            self.canvas.draw_idle()

    def _draw_animate(self):
        self.canvas.restore_region(self.background)
        if self.ax.get_visible() and self.figThreshold.get_visible():
            self.ax.draw_artist(self.figThreshold)
        if self.figThresholdLabel.get_visible():
            self.ax.draw_artist(self.figThresholdLabel)
        self.canvas.blit(self.ax.bbox)

    def _set_animated(self, value):
        if self.animated != value:
            self.animated = value
            self.figThreshold.set_animated(value)
            self.figThresholdLabel.set_animated(value)
            if self.animated == True:
                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.ax.bbox)


class PlayBackMarker(QtCore.QObject):
    """Plots a vertical line marker on a SignalViewerWidget when
    signal is played to indicate the current position.

    Attributes:
        position: Current position of the marker.
        active: Indicates whether the marker is active or not.
    """

    def __init__(self, fig, parent, position=0.0, active=False):
        super(PlayBackMarker, self).__init__()
        self.fig = fig
        self.parent = parent
        self.position = position
        self.active = active

        # Set lines
        self.markers = []
        for ax in self.fig.axes:
            marker = ax.axvline(self.position)
            marker.set(color='k', lw=1, alpha=0.6)
            marker.set_visible(self.active)
            self.markers.append(marker)

        self.canvas = self.fig.canvas
        if self.active:
            self.parent.draw()

    def set_position(self, value):
        if value != self.position:
            self.position = value
            for marker in self.markers:
                marker.set_xdata(self.position)
            if self.active:
                self.parent.draw()

    def set_visible(self, value):
        if value != self.active:
            self.active = value
            for marker in self.markers:
                marker.set_visible(self.active)
            self.parent.draw()

    def get_visible(self):
        return self.active


class MiniMap(QtGui.QWidget):
    """Shows the entire signal and allows the user to navigate through it.

    Provides an scrollable selector over the entire signal.

    Attributes:
        xmin: Selector lower limit (measured in h-axis units).
        xmax: Selector upper limit (measured in h-axis units).
        step: Selector length (measured in h-axis units).
    """

    def __init__(self, parent, ax, record=None):
        super(MiniMap, self).__init__(parent)
        self.ax = ax

        self.xmin = 0.0
        self.xmax = 0.0
        self.step = 10.0
        self.xrange = np.array([])

        self.minimapFig = plt.figure()
        self.minimapFig.set_figheight(0.75)
        self.minimapFig.add_axes((0, 0, 1, 1))
        self.minimapCanvas = FigureCanvas(self.minimapFig)
        self.minimapCanvas.setFixedHeight(64)
        self.minimapSelector = self.minimapFig.axes[0].axvspan(0, self.step,
                                                               color='gray',
                                                               alpha=0.5,
                                                               animated=True)
        self.minimapSelection = self.minimapFig.axes[0].axvspan(0, self.step,
                                                                color='LightCoral',
                                                                alpha = 0.5,
                                                                animated=True)
        self.minimapSelection.set_visible(False)
        self.minimapBackground = []
        self.minimapSize = (self.minimapFig.bbox.width,
                            self.minimapFig.bbox.height)

        self.press_selector = None
        self.playback_marker = None
        self.minimapCanvas.mpl_connect('button_press_event', self.onpress)
        self.minimapCanvas.mpl_connect('button_release_event', self.onrelease)
        self.minimapCanvas.mpl_connect('motion_notify_event', self.onmove)

        # Animation related attrs.
        self.background = None
        self.animated = False

        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.minimapCanvas)

        # Animation related attributes
        self.parentViewer = parent

        # Set Markers dict
        self.markers = {}

        self.record = None
        if record is not None:
            self.set_record(record)

    def set_record(self, record, step):
        self.record = record
        self.step = step
        self.xrange = np.linspace(0, len(self.record.signal) / self.record.fs,
                                  num=len(self.record.signal), endpoint=False)
        self.xmin = self.xrange[0]
        self.xmax = self.xrange[-1]
        self.markers = {}

        ax = self.minimapFig.axes[0]
        ax.lines = []
        formatter = FuncFormatter(lambda x, pos: str(datetime.timedelta(seconds=x)))
        ax.xaxis.set_major_formatter(formatter)
        ax.grid(True, which='both')
        ax.plot(self.xrange, self.record.signal, color='black', rasterized=True)
        ax.set_xlim(self.xmin, self.xmax)
        plotting.adjust_axes_height(ax)
        # Set the playback marker
        self.playback_marker = PlayBackMarker(self.minimapFig, self)
        self.playback_marker.markers[0].set_animated(True)
        # Draw canvas
        self.minimapCanvas.draw()
        self.minimapBackground = self.minimapCanvas.copy_from_bbox(self.minimapFig.bbox)
        self.draw_animate()

    def onpress(self, event):
        self.press_selector = event
        xdata = round(self.get_xdata(event), 2)
        xmin = round(xdata - (self.step / 2.0), 2)
        xmax = round(xdata + (self.step / 2.0), 2)
        self.parentViewer._set_animated(True)
        self.set_selector_limits(xmin, xmax)

    def onrelease(self, event):
        self.press_selector = None

        # Finish parent animation
        self.parentViewer._set_animated(False)

    def onmove(self, event):
        if self.press_selector is not None:
            xdata = round(self.get_xdata(event), 2)
            xmin = round(xdata - (self.step / 2.0), 2)
            xmax = round(xdata + (self.step / 2.0), 2)
            self.set_selector_limits(xmin, xmax)

    def get_xdata(self, event):
        inv = self.minimapFig.axes[0].transData.inverted()
        xdata, _ = inv.transform((event.x, event.y))
        return xdata

    def set_selector_limits(self, xmin, xmax):
        step = xmax - xmin
        if step >= self.xmax - self.xmin:
            xleft = self.xmin
            xright = self.xmax
        if xmin < self.xmin:
            xleft = self.xmin
            xright = self.step
        elif xmax > self.xmax:
            xleft = self.xmax - step
            xright = self.xmax
        else:
            xleft = xmin
            xright = xmax
        if (xleft, xright) != (self.minimapSelector.xy[1, 0], self.minimapSelector.xy[2, 0]):
            self.step = step
            self.minimapSelector.xy[:2, 0] = xleft
            self.minimapSelector.xy[2:4, 0] = xright
            self.ax.set_xlim(xleft, xright)
            self.draw_animate()
        else:
            self.parentViewer.draw()

    def get_selector_limits(self):
        return self.minimapSelector.xy[0, 0], self.minimapSelector.xy[2, 0]

    def draw(self):
        self.draw_animate()

    def draw_animate(self):
        size = self.minimapFig.bbox.width, self.minimapFig.bbox.height
        if size != self.minimapSize:
            self.minimapSize = size
            self.minimapCanvas.draw()
            self.minimapBackground = self.minimapCanvas.copy_from_bbox(self.minimapFig.bbox)
        self.minimapCanvas.restore_region(self.minimapBackground)
        self.minimapFig.draw_artist(self.minimapSelection)
        self.minimapFig.draw_artist(self.minimapSelector)
        self.minimapFig.draw_artist(self.playback_marker.markers[0])
        for marker in self.markers.values():
            self.minimapFig.draw_artist(marker)
        self.minimapCanvas.blit(self.minimapFig.bbox)

    def set_visible(self, value):
        self.minimapCanvas.setVisible(value)

    def get_visible(self):
        return self.minimapCanvas.isVisible()

    def set_selection_limits(self, xleft, xright):
        self.minimapSelection.xy[:2, 0] = xleft
        self.minimapSelection.xy[2:4, 0] = xright
        self.draw_animate()

    def set_selection_visible(self, value):
        self.minimapSelection.set_visible(value)
        self.draw_animate()

    def create_marker(self, key, position, **kwargs):
        if self.xmin <= position <= self.xmax:
            marker = self.minimapFig.axes[0].axvline(position, animated=True)
            self.markers[key] = marker
            self.markers[key].set(**kwargs)

    def set_marker_position(self, key, value):
        marker = self.markers.get(key)
        if marker is not None:
            if self.xmin <= value <= self.xmax:
                marker.set_xdata(value)

    def set_marker(self, key, **kwargs):
        marker = self.markers.get(key)
        if marker is not None:
            kwargs.pop("animated", None)  # marker's animated property must be always true to be drawn properly
            marker.set(**kwargs)

    def delete_marker(self, key):
        marker = self.markers.get(key)
        if marker is not None:
            self.minimapFig.axes[0].lines.remove(marker)
            self.markers.pop(key)


class SignalViewerWidget(QtGui.QWidget):
    """Shows different visualizations of a seismic signal (magnitude, envelope,
    spectrogram, characteristic function).
    Allows the user to manipulate it (navigate through it, zoom in/out,
    edit detected events, select threshold value, etc...)

    """

    CF_loaded = QtCore.Signal(bool)
    event_selected = QtCore.Signal(rc.Event)

    def __init__(self, parent, document=None):
        super(SignalViewerWidget, self).__init__(parent)

        self.document = document
        self.xmin = 0.0
        self.xmax = 0.0
        self.xleft = 0.0
        self.xright = 0.0
        self.time = np.array([])

        self.fs = 0.0
        self.signal = None
        self.envelope = None
        self.cf = None
        self.time = None
        self._signal_data = None
        self._envelope_data = None
        self._cf_data = None

        self.fig, _ = plt.subplots(3, 1)

        self.signal_ax = self.fig.axes[0]
        self.cf_ax = self.fig.axes[1]
        self.specgram_ax = self.fig.axes[2]

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding,
                                                    QtGui.QSizePolicy.Policy.Expanding))
        self.canvas.setMinimumHeight(320)
        self.graphArea = QtGui.QScrollArea(self)
        self.graphArea.setWidget(self.canvas)
        self.graphArea.setWidgetResizable(True)

        self.eventMarkers = {}
        self.last_right_clicked_event = None
        self.thresholdMarker = None
        self.playback_marker = None
        self.selector = SpanSelector(self.fig)
        self.minimap = MiniMap(self, self.signal_ax, None)

        # Load Spectrogram settings
        self.update_specgram_settings()

        # Animation related attributes
        self.background = None
        self.animated = False

        # Create context menus
        self.event_context_menu = QtGui.QMenu(self)
        self.takanami_on_event_action = QtGui.QAction("Apply Takanami to Event", self)
        self.takanami_on_event_action.setStatusTip("Refine event position by using Takanami algorithm")
        self.event_context_menu.addAction(self.takanami_on_event_action)
        self.takanami_on_event_action.triggered.connect(self.apply_takanami_to_selected_event)

        self.selection_context_menu = QtGui.QMenu(self)
        self.create_event_action = QtGui.QAction("Create New Event on Selection", self)
        self.create_event_action.setStatusTip("Create a new event on selection")
        self.takanami_on_selection_action = QtGui.QAction("Apply Takanami to Selection", self)
        self.takanami_on_selection_action.setStatusTip("Apply Takanami algorithm to selection")
        self.selection_context_menu.addAction(self.create_event_action)
        self.selection_context_menu.addAction(self.takanami_on_selection_action)
        self.create_event_action.triggered.connect(self.create_event_on_selection)
        self.takanami_on_selection_action.triggered.connect(self.apply_takanami_to_selection)

        # format axes
        formatter = FuncFormatter(lambda x, pos: clt.float_secs_2_string_date(x))
        for ax in self.fig.axes:
            ax.callbacks.connect('xlim_changed', self.on_xlim_change)
            ax.xaxis.set_major_formatter(formatter)
            plt.setp(ax.get_xticklabels(), visible=True)
            ax.grid(True, which='both')
        self.specgram_ax.callbacks.connect('ylim_changed', self.on_ylim_change)
        self.specgram_ax.set_xlabel('Time (seconds)')
        self.signal_ax.set_ylabel('Signal Amp.')
        self.cf_ax.set_ylabel('CF Amp.')
        self.specgram_ax.set_ylabel('Frequency (Hz)')

        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.graphArea)
        self.layout.addWidget(self.minimap)

        self.selector.toggled.connect(self.minimap.set_selection_visible)
        self.selector.valueChanged.connect(self.minimap.set_selection_limits)
        self.selector.right_clicked.connect(self.on_selector_right_clicked)

        if self.document is not None:
            self.set_record(document)

    @property
    def data_loaded(self):
        return self.document is not None

    def set_record(self, document, step=120.0):
        self.document = document
        self.fs = self.document.record.fs
        self.signal = self.document.record.signal
        self.envelope = env.envelope(self.signal)
        self.cf = self.document.record.cf
        self.time = np.linspace(0, len(self.signal) / self.fs, num=len(self.signal), endpoint=False)
        self.xmax = self.time[-1]
        # Draw minimap
        self.minimap.set_record(self.document.record, step)
        # Plot signal
        self._signal_data = self.signal_ax.plot(self.time,
                                                  self.signal,
                                                  color='black',
                                                  rasterized=True)[0]
        # Plot envelope
        self._envelope_data = self.signal_ax.plot(self.time,
                                                    self.envelope,
                                                    color='red',
                                                    rasterized=True)[0]
        plotting.adjust_axes_height(self.signal_ax)
        # Plot CF
        cf_loaded = (self.cf.size != 0)
        self.set_cf_visible(cf_loaded)
        self.CF_loaded.emit(cf_loaded)
        self._cf_data = self.cf_ax.plot(self.time[:len(self.cf)],
                                              self.cf,
                                              color='black', rasterized=True)[0]
        plotting.adjust_axes_height(self.signal_ax)
        self.thresholdMarker = ThresholdMarker(self.cf_ax)
        # Plot espectrogram
        plotting.plot_specgram(self.specgram_ax, self.signal, self.fs,
                               nfft=self.specgram_windowlen,
                               noverlap=self.specgram_noverlap,
                               window=self.specgram_window)
        # Set the span selector
        self.selector.fs = self.fs
        self.selector.set_active(False)
        self.selector.set_selection_limits(self.xmin, self.xmax)
        # Set the playback marker
        self.playback_marker = PlayBackMarker(self.fig, self)
        # Set the initial xlimits
        self.set_xlim(0, step)
        self.subplots_adjust()

    def unset_record(self):
        self.document = None
        self.signal = None
        self.envelope = None
        self.cf = None
        self.time = None
        self._signal_data = None
        self._envelope_data = None
        self._cf_data = None
        self.xmin, self.xmax = 0.0, 0.0
        # Clear axes
        self.signal_ax.lines = []
        self.cf_ax.lines = []
        self.specgram_ax.lines = []
        self.specgram_ax.images = []

        self.CF_loaded.emit(False)

    def update_cf(self):
        if self.data_loaded:
            self.cf = self.document.record.cf
            self._cf_data.set_xdata(self.time[:len(self.cf)])
            self._cf_data.set_ydata(self.cf)
            plotting.adjust_axes_height(self.cf_ax)
            cf_loaded = (self.cf.size != 0)
            self.CF_loaded.emit(cf_loaded)
            self.set_cf_visible(cf_loaded)

    def create_event(self, event):
        if event not in self.eventMarkers:
            marker = EventMarker(self.fig, self.minimap, self.document, event)
            self.eventMarkers[event] = marker
            marker.event_selected.connect(self.event_selected.emit)
            marker.right_clicked.connect(self.on_event_right_clicked)

    def delete_event(self, event):
        self.eventMarkers[event].remove()
        self.eventMarkers.pop(event)

    def update_event(self, event):
        self.eventMarkers[event].update()

    def set_xlim(self, l, r):
        xmin = max(0, l)
        xmax = min(self.xmax, r)
        self.signal_ax.set_xlim(xmin, xmax)

    def on_xlim_change(self, ax):
        xmin, xmax = ax.get_xlim()
        if (self.xleft, self.xright) != (xmin, xmax):
            self.xleft, self.xright = xmin, xmax
            if self.xmin <= xmin <= xmax <= self.xmax:
                # Update minimap selector
                if (xmin, xmax) != self.minimap.get_selector_limits():
                    self.minimap.set_selector_limits(xmin, xmax)

                # Update axes
                for axes in self.fig.axes:
                    if ax != axes:
                        axes.set_xlim(xmin, xmax)

                # Update data
                xmin = int(max(0, xmin) * self.fs)
                xmax = int(min(self.xmax, xmax) * self.fs)

                pixel_width = np.ceil(self.fig.get_figwidth() * self.fig.get_dpi())

                if self._signal_data is not None:
                    x_data, y_data = plotting.reduce_data(self.time, self.signal,
                                                          pixel_width, xmin, xmax)
                    self._signal_data.set_xdata(x_data)
                    self._signal_data.set_ydata(y_data)

                if self._envelope_data is not None:
                    x_data, y_data = plotting.reduce_data(self.time, self.envelope,
                                                          pixel_width, xmin, xmax)
                    self._envelope_data.set_xdata(x_data)
                    self._envelope_data.set_ydata(y_data)

                if self._cf_data is not None and self.cf_ax.get_visible():
                    x_data, y_data = plotting.reduce_data(self.time[:len(self.cf)],
                                                          self.cf, pixel_width,
                                                          xmin, xmax)
                    self._cf_data.set_xdata(x_data)
                    self._cf_data.set_ydata(y_data)
                # Draw graph
                self.draw()

            else:
                xmin = max(self.xmin, xmin)
                xmax = min(self.xmax, xmax)
                ax.set_xlim(xmin, xmax)

    def on_ylim_change(self, ax):
        if self.data_loaded:
            if ax == self.specgram_ax:
                ymin, ymax = ax.get_ylim()
                nyquist_freq = (self.fs / 2.0)
                if ymin < 0.0:
                    ax.set_ylim(0.0, ymax)
                elif ymax > nyquist_freq:
                    ax.set_ylim(ymin, nyquist_freq)

    def set_event_selection(self, events):
        for event in self.eventMarkers:
            self.eventMarkers[event].set_selected(event in events)
        self.draw()
        self.minimap.draw()

    def set_position(self, pos):
        """"""
        xmin, xmax = self.signal_ax.get_xlim()
        mrange = xmax - xmin
        l, r = pos - mrange / 2.0, pos + mrange / 2.0
        if l < self.xmin:
            l, r = self.xmin, mrange
        elif r > self.xmax:
            l, r = self.xmax - mrange, self.xmax
        self.set_xlim(l, r)

    def goto_event(self, event):
        if event in self.eventMarkers:
            self.set_position(event.time / self.fs)

    def showEvent(self, event):
        self.draw()
        self.minimap.draw_animate()

    def resizeEvent(self, event):
        self.draw()
        self.minimap.draw_animate()

    def set_signal_amplitude_visible(self, show_sa):
        if self._signal_data is not None and self._envelope_data is not None:
            if self._signal_data.get_visible() != show_sa:
                self._signal_data.set_visible(show_sa)
                show_axis = (self._signal_data.get_visible() +
                             self._envelope_data.get_visible())
                self.signal_ax.set_visible(show_axis)
                if self.data_loaded:
                    self.subplots_adjust()
                    self.draw()

    def set_signal_envelope_visible(self, show_se):
        if self._signal_data is not None and self._envelope_data is not None:
            if self._envelope_data.get_visible() != show_se:
                self._envelope_data.set_visible(show_se)
                show_axis = (self._signal_data.get_visible() +
                             self._envelope_data.get_visible())
                self.signal_ax.set_visible(show_axis)
                if self.data_loaded:
                    self.subplots_adjust()
                    self.draw()

    def set_cf_visible(self, show_cf):
        if self.cf_ax.get_visible() != show_cf:
            if self.data_loaded:
                if len(self.cf) <= 0:
                    self.cf_ax.set_visible(False)
                else:
                    self.cf_ax.set_visible(show_cf)
                    self.subplots_adjust()
                    self.draw()

    def set_espectrogram_visible(self, show_eg):
        if self.specgram_ax.get_visible() != show_eg:
            self.specgram_ax.set_visible(show_eg)
            if self.data_loaded:
                self.subplots_adjust()
                self.draw()

    def set_minimap_visible(self, show_mm):
        if self.minimap.get_visible() != show_mm:
            self.minimap.set_visible(show_mm)
            self.minimap.draw_animate()

    def set_threshold_visible(self, show_thr):
        if self.thresholdMarker:
            if self.thresholdMarker.get_visible() != show_thr:
                self.thresholdMarker.set_visible(show_thr)
                self.draw()

    def subplots_adjust(self):
        visible_subplots = [ax for ax in self.fig.get_axes() if ax.get_visible()]
        for i, ax in enumerate(visible_subplots):
            correct_geometry = (len(visible_subplots), 1, i + 1)
            if correct_geometry != ax.get_geometry():
                ax.change_geometry(len(visible_subplots), 1, i + 1)
        # Adjust space between subplots
        self.fig.subplots_adjust(left=0.06, right=0.95, bottom=0.14,
                                 top=0.95, hspace=0.22)

    def get_selector_limits(self):
        return self.selector.get_selector_limits()

    def set_selector_limits(self, xleft, xright):
        self.selector.set_selector_limits(xleft, xright)

    def set_selection_enabled(self, value):
        self.selector.set_enabled(value)

    def set_playback_position(self, position):
        if self.playback_marker is not None:
            self.playback_marker.set_position(position)
            self.minimap.playback_marker.set_position(position)

    def set_playback_marker_visible(self, show_marker):
        if self.playback_marker is not None:
            self.playback_marker.set_visible(show_marker)
            self.minimap.playback_marker.set_visible(show_marker)

    def on_event_right_clicked(self, event):
        self.last_right_clicked_event = event
        self.event_context_menu.exec_(QtGui.QCursor.pos())

    def apply_takanami_to_selected_event(self):
        takanamidialog.TakanamiDialog(self.document,
                                      seismic_event=self.last_right_clicked_event).exec_()

    def apply_takanami_to_selection(self):
        xleft, xright = self.get_selector_limits()
        takanamidialog.TakanamiDialog(self.document, xleft, xright).exec_()

    def create_event_on_selection(self):
        xleft, xright = self.get_selector_limits()
        xleft, xright = xleft * self.fs, xright * self.fs
        cf = self.cf[xleft:xright]
        if cf.size > 0:
            time = (xleft + np.argmax(cf))
        else:
            time = (xleft + ((xright - xleft) / 2.0))
        self.document.createEvent(time=time)

    def draw(self):
        if self.animated:
            self._draw_animate()
        else:
            self.canvas.draw_idle()

    def _draw_animate(self):
        self.canvas.restore_region(self.background)
        for artist in self._get_animated_artists():
            if artist.get_visible():
                ax = artist.get_axes()
                if ax is not None:
                    if artist.get_axes().get_visible():
                        self.fig.draw_artist(artist)
                else:
                    self.fig.draw_artist(artist)
        self.canvas.blit(self.fig.bbox)

    def _set_animated(self, value):
        if self.animated != value:
            self.animated = value
            for artist in self._get_animated_artists():
                artist.set_animated(value)
            if self.animated == True:
                images = []
                for ax in self.fig.axes:
                    images.extend(ax.images)
                for image in images:
                    image.set_visible(False)

                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.fig.bbox)

                for image in images:
                    image.set_visible(True)

    def _get_animated_artists(self):
        artists = []
        for ax in self.fig.axes:
            artists.extend(ax.images)
            artists.extend(ax.lines)
            artists.append(ax.xaxis)
            artists.append(ax.yaxis)
            artists.extend(ax.patches)
            artists.extend(ax.spines.values())
        for artist in artists:
            yield artist

    def update_specgram_settings(self):
        # load specgram settings
        settings = QtCore.QSettings(_organization, _application_name)

        settings.beginGroup("specgram_settings")
        self.specgram_windowlen = int(settings.value('window_len', settingsdialog.SPECGRAM_WINDOW_LENGTHS[4]))
        self.specgram_noverlap = int(settings.value('noverlap', self.specgram_windowlen / 2))
        self.specgram_window = settings.value('window', plotting.SPECGRAM_WINDOWS[2])
        settings.endGroup()

        if self.data_loaded:
            # Plot espectrogram
            self.specgram_ax.images = []
            # Save x-axis limits
            limits = self.signal_ax.get_xlim()
            # Draw spectrogram
            plotting.plot_specgram(self.specgram_ax, self.signal, self.fs,
                                   nfft=self.specgram_windowlen,
                                   noverlap=self.specgram_noverlap,
                                   window=self.specgram_window)
            # Restore x-axis limits
            self.signal_ax.set_xlim(*limits)

    def paintEvent(self, paintEvent):
        super(SignalViewerWidget, self).paintEvent(paintEvent)

    def on_selector_right_clicked(self):
        xleft, xright = self.get_selector_limits()
        self.takanami_on_selection_action.setEnabled((xright - xleft) >=
                                                     (takanamidialog.MINIMUM_MARGIN_IN_SECS * 2))
        self.selection_context_menu.exec_(QtGui.QCursor.pos())


