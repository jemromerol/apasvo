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

import numpy as np
import matplotlib
matplotlib.rcParams['backend'] = 'qt4agg'
matplotlib.rcParams['backend.qt4'] = 'PySide'
matplotlib.rcParams['patch.antialiased'] = False
matplotlib.rcParams['figure.dpi'] = 65
matplotlib.rcParams['agg.path.chunksize'] = 80000
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid.anchored_artists import AnchoredText

from apasvo.utils import plotting
from apasvo.utils import clt


class TracePlot(QtCore.QObject):

    def __init__(self, parent, trace, fig_nrows=1, fig_ncols=1, ax_pos=1):
        super(TracePlot, self).__init__()
        self.parent = parent
        self.fig = parent.fig
        self.ax = self.fig.add_subplot(fig_nrows, fig_ncols, ax_pos, visible=False)
        self.trace = trace
        # Get trace dataseries
        self.signal = trace.signal
        self.time = np.linspace(0, len(self.signal) / trace.fs, num=len(self.signal), endpoint=False)
        self.xmin, self.xmax = 0, self.time[-1]
        # Plot current data
        self._plot_data = self.ax.plot(self.time, self.signal, color='black', rasterized=True)[0]
        self.ax.callbacks.connect('xlim_changed', self.on_xlim_change)
        self.ax.set_xlim(self.xmin, self.xmax)
        # Format axes
        axes_formatter = FuncFormatter(lambda x, pos: clt.float_secs_2_string_date(x, trace.starttime))
        self.ax.xaxis.set_major_formatter(axes_formatter)
        plt.setp(self.ax.get_xticklabels(), visible=False)
        plt.setp(self.ax.get_yticklabels(), visible=False)
        self.ax.grid(True, which='both')
        # Set event markers
        self.marker_select_color = 'r'
        self.marker_color = 'b'
        self.markers = {}
        self.update_markers()
        # Selection parameters
        self.selected = False
        self.selector = self.ax.axvspan(0, self.xmax, fc='LightCoral', ec='r', alpha=0.5, visible=False)#, animated=True)
        # Place legend
        at = AnchoredText(self.trace.short_name, prop=dict(size=12), frameon=True, loc=2)
        at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
        self.ax.add_artist(at)

    def on_xlim_change(self, ax):
        xmin, xmax = ax.get_xlim()
        if self.xmin <= xmin <= xmax <= self.xmax:
            # Update data
            xmin = int(max(0, self.xmin) * self.trace.fs)
            xmax = int(min(self.xmax, xmax) * self.trace.fs)
            pixel_width = np.ceil(self.fig.get_figwidth() * self.fig.get_dpi())
            x_data, y_data = plotting.reduce_data(self.time, self.signal, pixel_width, xmin, xmax)
            self._plot_data.set_xdata(x_data)
            self._plot_data.set_ydata(y_data)
        else:
            xmin = max(self.xmin, xmin)
            xmax = min(self.xmax, xmax)
            ax.set_xlim(xmin, xmax)

    def create_marker(self, event, **kwargs):
        event_id = event.resource_id.uuid
        position = event.stime / self.trace.fs
        marker = self.ax.axvline(position, color=self.marker_color, ls='--', lw=3, visible=False)#, animated=True)
        self.markers[event_id] = marker
        self.markers[event_id].set(**kwargs)

    def delete_marker(self, event_id):
        marker = self.markers[event_id]
        if marker is not None:
            self.ax.lines.remove(marker)
            self.markers.pop(event_id)

    def update_markers(self, draw=False):
        for event_id in self.markers.keys():
            self.delete_marker(event_id)
        for event in self.trace.events:
            self.create_marker(event)
        if draw:
            self.parent.draw()

    def set_selected_marker(self, selected):
        color = self.marker_select_color if selected else self.marker_color
        for marker in self.markers:
            marker.set(color=color)

    def set_event_selection(self, event_list):
        event_id_list = [event.resource_id.uuid for event in event_list]
        for event_id in self.markers.keys():
            self.markers[event_id].select_marker(event_id in event_id_list)
        self.parent.draw()

    def set_selected(self, selected):
        if self.selected != selected:
            self.selected = selected
            if self.selected:
                self.selector.set_visible(True)
                # self.ax.set_axis_bgcolor('LightCoral')
            else:
                self.selector.set_visible(False)
                # self.ax.set_axis_bgcolor('white')

    def remove(self):
        self.fig.delaxes(self.ax)
        self.parent.subplots_adjust()
        self.parent.draw()


class StreamViewerWidget(QtGui.QWidget):
    """Shows the entire signal and allows the user to navigate through it.

    Provides an scrollable selector over the entire signal.

    Attributes:
        xmin: Selector lower limit (measured in h-axis units).
        xmax: Selector upper limit (measured in h-axis units).
        step: Selector length (measured in h-axis units).
    """

    trace_selected = QtCore.Signal(int)
    selection_made = QtCore.Signal(bool)

    def __init__(self, parent, stream=None):
        super(StreamViewerWidget, self).__init__(parent)

        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding,
                                                    QtGui.QSizePolicy.Policy.Expanding))
        self.canvas.setMinimumHeight(320)
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.canvas.setFocus()
        self.graphArea = QtGui.QScrollArea(self)
        self.graphArea.setWidget(self.canvas)
        self.graphArea.setWidgetResizable(True)
        self.graphArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.graphArea)

        # Animation related attrs.
        self.background = []
        self.animated = False
        self.size = (self.fig.bbox.width, self.fig.bbox.height)

        # Set TracePlot list
        self.trace_plots = []

        self.stream = None
        if stream is not None:
            self.set_stream(stream)

        # Event handling
        self.visible_axes = []
        self._selected_traces = set()
        self.shift_pressed = False
        self.press_selector = None
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_move)
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.on_key_release)

    @property
    def selected_traces(self):
        if self.stream is not None:
            return [self.stream.traces[i] for i in self._selected_traces]
        return []

    def on_move(self, event):
        axes_selected = False
        for i, axes in enumerate(self.fig.axes):
            if axes.get_visible():
                ymin, ymax = axes.get_position().ymin, axes.get_position().ymax
                xmin, xmax = axes.get_position().xmin, axes.get_position().xmax
                xfig, yfig = self._event_to_fig_coords(event)
                if ymin <= yfig <= ymax and xmin <= xfig <= xmax:
                    self.canvas.setToolTip(self.stream.traces[i].name)
                    axes_selected = True
                    break
        if not axes_selected:
            self.canvas.setToolTip("")

    def on_key_press(self, event):
        if event.key == 'control':
            self.shift_pressed = True

    def on_key_release(self, event):
        self.shift_pressed = False

    def on_press(self, event):
        trace_selected = False
        if event.button == 1:# and event.dblclick:
            for i, ax in enumerate(self.fig.axes):
                if ax.get_visible():
                    ymin, ymax = ax.get_position().ymin, ax.get_position().ymax
                    xmin, xmax = ax.get_position().xmin, ax.get_position().xmax
                    xfig, yfig = self._event_to_fig_coords(event)
                    if ymin <= yfig <= ymax and xmin <= xfig <= xmax:
                        trace_selected = True
                        if self.shift_pressed:
                            if self._selected_traces:
                                self.trace_selected.emit(i)
                                self.selection_made.emit(True)
                            self._selected_traces.add(i)
                        else:
                            self.trace_selected.emit(i)
                            self.selection_made.emit(True)
                            self._selected_traces = {i}
                        break
            # if the user clicked out of any trace (and he's not using shift), then deselect all
            if not trace_selected and not self.shift_pressed:
                self._selected_traces = set()
                self.selection_made.emit(False)
            # Now update selection status on plots
            for i, plot in enumerate(self.trace_plots):
                plot.set_selected(i in self._selected_traces)
            self.draw()

    def _event_to_fig_coords(self, event):
        inv = self.fig.transFigure.inverted()
        return inv.transform((event.x, event.y))

    def set_stream(self, stream):
        self.stream = stream
        self._selected_traces = set()
        # Clear canvas
        for plot in self.trace_plots:
            plot.remove()
        self.trace_plots = []
        # Plot stream traces
        for i, trace in enumerate(self.stream.traces):
            self.trace_plots.append(TracePlot(self, trace, fig_nrows=len(stream), ax_pos=i + 1))
        # Draw canvas
        self.subplots_adjust()
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.draw()

    def draw(self):
        self.canvas.draw()
        #self.draw_animate()

    def draw_animate(self):
        size = self.fig.bbox.width, self.fig.bbox.height
        if size != self.size:
            self.size = size
            self.canvas.draw()
            self.background = self.canvas.copy_from_bbox(self.fig.bbox)
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
            if artist.get_animated():
                yield artist

    def set_visible(self, value):
        self.canvas.setVisible(value)

    def get_visible(self):
        return self.canvas.isVisible()

    def remove_trace(self, idx):
        self.trace_plots.pop(idx).remove()

    def subplots_adjust(self):
        visible_subplots = [ax for ax in self.fig.get_axes() if ax.get_visible()]
        for i, ax in enumerate(visible_subplots):
            correct_geometry = (len(visible_subplots), 1, i + 1)
            if correct_geometry != ax.get_geometry():
                ax.change_geometry(len(visible_subplots), 1, i + 1)
        # Adjust space between subplots
        self.fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02,
                                 top=0.98, hspace=0.05)

    def showEvent(self, event):
        self.draw()

    def resizeEvent(self, event):
        self.draw()

    def update_markers(self):
        for plot in self.trace_plots:
            plot.update_markers()
        self.draw()

    def visualize_stream_range(self, start_trace=None, end_trace=None):
        for i, ax in enumerate(self.fig.axes):
            ax.set_visible(start_trace <= i < end_trace)
        self.subplots_adjust()
        self.canvas.draw()
