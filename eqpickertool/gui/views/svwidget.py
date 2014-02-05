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
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np
import datetime

from eqpickertool.picking import envelope as env
from eqpickertool.picking import record as rc
from eqpickertool.utils import plotting


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

#         bbox = dict(boxstyle="round", fc="LightCoral", ec="r", alpha=0.8)
#         self.selectorLeftLabel = matplotlib.text.Text(0, 0, "0.00", bbox=bbox)
#         self.selectorLeftLabel.set_visible(False)
#         self.selectorRightLabel = matplotlib.text.Text(0, 0, "0.00", bbox=bbox)
#         self.selectorRightLabel.set_visible(False)
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
                self.set_selector_limits(xleft, xright, adjust_to_viewport=True)

    def get_xdata(self, event):
        inv = self.fig.axes[0].transData.inverted()
        xdata, _ = inv.transform((event.x, event.y))
        return xdata

    def set_selector_limits(self, xleft, xright, adjust_to_viewport=False):
        if (xleft, xright) != (self.xleft, self.xright):
            if adjust_to_viewport:
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
        if value != self.active:
            self.active = value
            self.toggled.emit(value)
            for s in self.selectors:
                s.set_visible(value)
            self.fig.canvas.draw_idle()


class EventMarker(QtCore.QObject):
    """Plots a vertical line marker to indicate the arrival time of
    a detected event on a SignalViewerWidget object.

    Attributes:
        event: Marked event.

    Signals:
        valueChanged: 'event' arrival time changed.
    """

    def __init__(self, fig, document, event):
        super(EventMarker, self).__init__()
        self.fig = fig
        self.event = event
        self.document = document
        self.position = self.event.time

        self.markers = []
        # draw markers
        for ax in self.fig.axes:
            marker = ax.axvline(self.event.time / self.event.record.fs)
            marker.set(color='r', ls='--', lw=2, alpha=0.8, picker=5)
            self.markers.append(marker)
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
        # draw canvas
        self.canvas.draw_idle()

    def onpick(self, pick_event):
        if pick_event.artist in self.markers:
            if not self.canvas.widgetlock.locked():
                self.canvas.widgetlock(self)
                self.pick_event = pick_event
                xfig, yfig = self._event_to_fig_coords(pick_event.mouseevent)
                self.position_label.set_position((xfig, yfig))
                self.position_label.set_visible(True)
                self.canvas.draw_idle()

    def onrelease(self, mouse_event):
        if self.canvas.widgetlock.isowner(self):
            self.position_label.set_visible(False)
            self.pick_event = None
            self.canvas.draw_idle()
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
            self.canvas.draw_idle()

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
            if 0 <= self.position <= len(self.event.record.signal):
                self.position = time_in_samples
                time_in_seconds = time_in_samples / float(self.event.record.fs)
                for marker in self.markers:
                    marker.set_xdata(time_in_seconds)
                t = str(datetime.timedelta(seconds=time_in_seconds))
                if 0 <= self.position < len(self.event.record.cf):
                    cf_value = self.event.record.cf[self.position]
                else:
                    cf_value = np.nan
                self.position_label.set_text("Time: %s seconds\nCF value: %.4g" %
                                             (t[:-3], cf_value))

    def redraw(self):
        self.position = self.event.time
        for marker in self.markers:
            marker.set_xdata(self.position / float(self.event.record.fs))
        self.canvas.draw_idle()

    def remove(self):
        for ax, marker in zip(self.fig.axes, self.markers):
            ax.lines.remove(marker)
        self.canvas.draw_idle()


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
        if self.threshold != value:
            if value >= 0:
                self.threshold = value
                self.thresholdChanged.emit(self.threshold)
                self.figThreshold.set_ydata(self.threshold)
                self.figThresholdLabel.set_text("Threshold: %.2f" % self.threshold)
                if self.figThreshold.get_visible():
                    self.canvas.draw_idle()

    def set_visible(self, value):
        if self.active != value:
            self.figThreshold.set_visible(value)
            self.active = value
            self.canvas.draw_idle()

    def get_visible(self):
        return self.active


class PlayBackMarker(QtCore.QObject):
    """Plots a vertical line marker on a SignalViewerWidget when
    signal is played to indicate the current position.

    Attributes:
        position: Current position of the marker.
        active: Indicates whether the marker is active or not.
    """

    def __init__(self, fig, position=0.0, active=False):
        super(PlayBackMarker, self).__init__()
        self.fig = fig
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
            self.canvas.draw_idle()

    def set_position(self, value):
        if value != self.position:
            self.position = value
            for marker in self.markers:
                marker.set_xdata(self.position)
            if self.active:
                self.canvas.draw_idle()

    def set_visible(self, value):
        if value != self.active:
            self.active = value
            for marker in self.markers:
                marker.set_visible(self.active)
            self.canvas.draw_idle()

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
        self.record = record
        self.step = step
        self.xrange = np.arange(len(self.record.signal)) / self.record.fs
        self.xmin = self.xrange[0]
        self.xmax = self.xrange[-1]

        ax = self.minimapFig.axes[0]
        ax.lines = []
        formatter = FuncFormatter(lambda x, pos: str(datetime.timedelta(seconds=x)))
        ax.xaxis.set_major_formatter(formatter)
        ax.grid(True, which='both')
        ax.plot(self.xrange, self.record.signal, color='black', rasterized=True)
        ax.set_xlim(self.xmin, self.xmax)
        # Draw canvas
        self.minimapCanvas.draw()
        self.minimapBackground = self.minimapCanvas.copy_from_bbox(self.minimapFig.bbox)
        self.draw_animate()

    def onpress(self, event):
        self.press_selector = event
        xdata = round(self.get_xdata(event), 2)
        xmin = round(xdata - (self.step / 2.0), 2)
        xmax = round(xdata + (self.step / 2.0), 2)
        self.set_selector_limits(xmin, xmax)

    def onrelease(self, event):
        self.press_selector = None

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

    def get_visible(self):
        return self.minimapCanvas.isVisible()

    def set_selection_limits(self, xleft, xright):
        self.minimapSelection.xy[:2, 0] = xleft
        self.minimapSelection.xy[2:4, 0] = xright
        self.draw_animate()

    def set_selection_visible(self, value):
        self.minimapSelection.set_visible(value)
        self.draw_animate()


class SignalViewerWidget(QtGui.QWidget):
    """Shows different visualizations of a seismic signal (magnitude, envelope,
    spectrogram, characteristic function).
    Allows the user to manipulate it (navigate through it, zoom in/out,
    edit detected events, select threshold value, etc...)

    """

    CF_loaded = QtCore.Signal(bool)

    def __init__(self, parent, document=None):
        super(SignalViewerWidget, self).__init__(parent)

        self.xmin = 0.0
        self.xmax = 0.0
        self.time = np.array([])

        self.fs = 0.0
        self.signal = None
        self.envelope = None
        self.cf = None
        self.time = None
        self._signal_data = None
        self._envelope_data = None
        self._cf_data = None

        self.fig, _ = plt.subplots(3, 1, sharex=True)

        self.signal_ax = self.fig.axes[0]
        self.cf_ax = self.fig.axes[1]
        self.specgram_ax = self.fig.axes[2]

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumSize(self.canvas.size())
        self.graphArea = QtGui.QScrollArea(self)
        self.graphArea.setWidgetResizable(True)
        self.graphArea.setWidget(self.canvas)

        self.eventMarkers = {}
        self.thresholdMarker = None
        self.playback_marker = None
        self.selector = SpanSelector(self.fig)
        self.minimap = MiniMap(self, self.signal_ax, None)

        # format axes
        formatter = FuncFormatter(lambda x, pos: str(datetime.timedelta(seconds=x)))
        for ax in self.fig.axes:
            ax.callbacks.connect('xlim_changed', self.on_xlim_change)
            ax.xaxis.set_major_formatter(formatter)
            plt.setp(ax.get_xticklabels(), visible=True)
            ax.grid(True, which='both')
        self.specgram_ax.callbacks.connect('ylim_changed', self.on_ylim_change)
        self.specgram_ax.set_xlabel('Time (seconds)')
        self.signal_ax.set_ylabel('Signal Amplitude')
        self.cf_ax.set_ylabel('CF Amplitude')
        self.specgram_ax.set_ylabel('Frequency (Hz)')

        # Adjust space between subplots
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.1,
                                 top=0.95, hspace=0.2)

        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.graphArea)
        self.layout.addWidget(self.minimap)

        self.selector.toggled.connect(self.minimap.set_selection_visible)
        self.selector.valueChanged.connect(self.minimap.set_selection_limits)

        self.document = document
        if self.document is not None:
            self.set_record(document)

    @property
    def data_loaded(self):
        return self.document is not None

    def set_record(self, document, step=20.0):
        self.document = document
        self.fs = self.document.record.fs
        self.signal = self.document.record.signal
        self.envelope = env.envelope(self.signal)
        self.cf = self.document.record.cf
        self.time = np.arange(len(self.signal)) / self.fs
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
        plotting.plot_specgram(self.specgram_ax, self.signal, self.fs)
        # Set the span selector
        self.selector.set_active(False)
        self.selector.set_selection_limits(self.xmin, self.xmax)
        # Set the playback marker
        self.playback_marker = PlayBackMarker(self.fig)
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
            self.eventMarkers[event] = EventMarker(self.fig, self.document, event)

    def delete_event(self, event):
        self.eventMarkers[event].remove()
        self.eventMarkers.pop(event)

    def update_event(self, event):
        self.eventMarkers[event].redraw()

    def set_xlim(self, l, r):
        xmin = max(0, l)
        xmax = min(self.xmax, r)
        self.signal_ax.set_xlim(xmin, xmax)

    def on_xlim_change(self, ax):
        xmin, xmax = ax.get_xlim()
        if self.xmin <= xmin <= xmax <= self.xmax:
            # Update minimap selector
            if (xmin, xmax) != self.minimap.get_selector_limits():
                self.minimap.set_selector_limits(xmin, xmax)

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
            self.draw_idle()
        else:
            xmin = max(self.xmin, xmin)
            xmax = min(self.xmax, xmax)
            ax.set_xlim(xmin, xmax)

    def on_ylim_change(self, ax):
        if self.data_loaded:
            if ax == self.specgram_ax:
                ymin, ymax = ax.get_ylim()
                nyquist_freq = (self.fs / 2.0)
                if not 0.0 <= ymin <= ymax <= nyquist_freq:
                    ymin = max(0.0, ymin)
                    ymax = min(nyquist_freq, ymax)
                    ax.set_ylim(ymin, ymax)

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

    def draw_idle(self):
        self.canvas.draw_idle()
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
                    self.draw_idle()

    def set_signal_envelope_visible(self, show_se):
        if self._signal_data is not None and self._envelope_data is not None:
            if self._envelope_data.get_visible() != show_se:
                self._envelope_data.set_visible(show_se)
                show_axis = (self._signal_data.get_visible() +
                             self._envelope_data.get_visible())
                self.signal_ax.set_visible(show_axis)
                if self.data_loaded:
                    self.subplots_adjust()
                    self.draw_idle()

    def set_cf_visible(self, show_cf):
        if self.cf_ax.get_visible() != show_cf:
            if self.data_loaded:
                if len(self.cf) <= 0:
                    self.cf_ax.set_visible(False)
                else:
                    self.cf_ax.set_visible(show_cf)
                    self.subplots_adjust()
                    self.draw_idle()

    def set_espectrogram_visible(self, show_eg):
        if self.specgram_ax.get_visible() != show_eg:
            self.specgram_ax.set_visible(show_eg)
            if self.data_loaded:
                self.subplots_adjust()
                self.draw_idle()

    def set_minimap_visible(self, show_mm):
        if self.minimap.get_visible() != show_mm:
            self.minimap.set_visible(show_mm)
            self.minimap.draw_animate()

    def set_threshold_visible(self, show_thr):
        if self.thresholdMarker:
            if self.thresholdMarker.get_visible() != show_thr:
                self.thresholdMarker.set_visible(show_thr)
                self.draw_idle()

    def subplots_adjust(self):
        visible_subplots = [ax for ax in self.fig.get_axes() if ax.get_visible()]
        for i, ax in enumerate(visible_subplots):
            ax.change_geometry(len(visible_subplots), 1, i + 1)

    def get_selector_limits(self):
        return self.selector.get_selector_limits()

    def set_selector_limits(self, xleft, xright):
        self.selector.set_selector_limits(xleft, xright)

    def set_playback_position(self, position):
        if self.playback_marker is not None:
            self.playback_marker.set_position(position)

    def set_playback_marker_visible(self, show_marker):
        if self.playback_marker is not None:
            self.playback_marker.set_visible(show_marker)
