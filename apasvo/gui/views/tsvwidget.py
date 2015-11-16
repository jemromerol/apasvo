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

from apasvo.utils import plotting
from apasvo.utils import clt


class StreamViewerWidget(QtGui.QWidget):
    """Shows the entire signal and allows the user to navigate through it.

    Provides an scrollable selector over the entire signal.

    Attributes:
        xmin: Selector lower limit (measured in h-axis units).
        xmax: Selector upper limit (measured in h-axis units).
        step: Selector length (measured in h-axis units).
    """

    trace_selected = QtCore.Signal(int)

    def __init__(self, parent, stream=None):
        super(StreamViewerWidget, self).__init__(parent)

        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding,
                                                    QtGui.QSizePolicy.Policy.Expanding))
        self.canvas.setMinimumHeight(320)
        self.graphArea = QtGui.QScrollArea(self)
        self.graphArea.setWidget(self.canvas)
        self.graphArea.setWidgetResizable(True)
        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.graphArea)

        self.press_selector = None
        self.canvas.mpl_connect('button_press_event', self.on_press)

        # Animation related attrs.
        self.background = []
        self.animated = False
        self.size = (self.fig.bbox.width, self.fig.bbox.height)

        # Set Markers dict
        self.markers = {}

        self.stream = None
        if stream is not None:
            self.set_stream(stream)

    def set_stream(self, stream):
        self.stream = stream
        # Clear canvas
        for axes in self.fig.axes:
            self.fig.delaxes(axes)
        # Plot stream traces
        for trace in stream:
            self._draw_trace(trace)
        # Plot event markers
        self.markers = {}
        for trace_idx, trace in enumerate(self.stream):
            for event in trace.events:
                event_id = event.resource_id.uuid
                self.create_marker(trace_idx, event_id, event.time)
        # Draw canvas
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.draw()

    def on_press(self, event):
        if event.button == 1:
            for i, axes in enumerate(self.fig.axes):
                ymin, ymax = axes.get_position().ymin, axes.get_position().ymax
                _, yfig = self._event_to_fig_coords(event)
                if ymin <= yfig <= ymax:
                    self.trace_selected.emit(i)
                    break

    def _event_to_fig_coords(self, event):
        inv = self.fig.transFigure.inverted()
        return inv.transform((event.x, event.y))

    def draw(self):
        self.subplots_adjust()
        self.canvas.draw()
#        self.draw_animate()

    def draw_animate(self):
        size = self.fig.bbox.width, self.fig.bbox.height
        if size != self.size:
            self.size = size
            self.canvas.draw()
            self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.canvas.restore_region(self.background)
        for trace_idx in self.markers.keys():
            for event_id in self.markers[trace_idx].keys():
                marker = self.markers[trace_idx].get(event_id)
                self.fig.draw_artist(marker)
        self.canvas.blit(self.fig.bbox)

    def set_visible(self, value):
        self.canvas.setVisible(value)

    def get_visible(self):
        return self.canvas.isVisible()

    def create_marker(self, trace_idx, event_id, position, **kwargs):
        marker = self.fig.axes[trace_idx].axvline(position, animated=True)
        if trace_idx not in self.markers:
            self.markers[trace_idx] = {}
        self.markers[trace_idx][event_id] = marker
        self.markers[trace_idx][event_id].set(**kwargs)

    def set_marker_position(self, trace_idx, event_id, value):
        marker = self.markers[trace_idx].get(event_id)
        if marker is not None:
            marker.set_xdata(value)

    def set_marker(self, trace_idx, event_id, **kwargs):
        marker = self.markers[trace_idx].get(event_id)
        if marker is not None:
            kwargs.pop("animated", None)  # marker's animated property must be always true to be drawn properly
            marker.set(**kwargs)

    def delete_marker(self, trace_idx, event_id, key):
        marker = self.markers[trace_idx].get(event_id)
        if marker is not None:
            self.fig.axes[trace_idx].lines.remove(marker)
            self.markers.pop(key)

    def _draw_trace(self, trace):
        if self.stream:
            # Get trace dataseries
            signal = trace.signal
            time = np.linspace(0, len(signal) / trace.fs, num=len(signal), endpoint=False)
            xmin, xmax = 0, time[-1]
            # If series are too long, reduce them
            # pixel_width = np.ceil(self.fig.get_figwidth() * self.fig.get_dpi())
            # x_data, y_data = plotting.reduce_data(time, signal, pixel_width, xmin, xmax)
            # Create axes with trace and add to existing axes
            trace_idx = self.stream.traces.index(trace)
            ax = self.fig.add_subplot(len(self.stream), 1, trace_idx)
            ax.set_xlim(xmin, xmax)
            ax.plot(time, signal, color='black', rasterized=True)
            ax.set_xlim(xmin, xmax)
            # Format axes
            axes_formatter = FuncFormatter(lambda x, pos: clt.float_secs_2_string_date(x, trace.starttime))
            ax.xaxis.set_major_formatter(axes_formatter)
            plt.setp(ax.get_xticklabels(), visible=True)
            ax.grid(True, which='both')

    def remove_trace(self, idx):
        self.fig.delaxes(self.fig.axes[idx])
        self.subplots_adjust()
        self.canvas.draw()

    def subplots_adjust(self):
        visible_subplots = [ax for ax in self.fig.get_axes() if ax.get_visible()]
        for i, ax in enumerate(visible_subplots):
            correct_geometry = (len(visible_subplots), 1, i + 1)
            if correct_geometry != ax.get_geometry():
                ax.change_geometry(len(visible_subplots), 1, i + 1)
        # Adjust space between subplots
        self.fig.subplots_adjust(left=0.06, right=0.95, bottom=0.14,
                                 top=0.95, hspace=0.22)
