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


class TracePlot(QtCore.QObject):

    trace_selected = QtCore.Signal(int)

    def __init__(self, parent, trace, fig_nrows=1, fig_ncols=1, ax_pos=1):
        super(TracePlot, self).__init__()
        self.parent = parent
        self.fig = parent.fig
        self.ax = self.fig.add_subplot(fig_nrows, fig_ncols, ax_pos)
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
        plt.setp(self.ax.get_xticklabels(), visible=True)
        self.ax.grid(True, which='both')
        # Set event markers
        self.markers = {}
        for event in self.trace.events:
            self.create_marker(event)
        # Event handling
        self.trace_selected.connect(self.parent.trace_selected)
        self.press_selector = None
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)

    def on_press(self, event):
        if event.button == 1:# and event.dblclick:
            ymin, ymax = self.ax.get_position().ymin, self.ax.get_position().ymax
            _, yfig = self._event_to_fig_coords(event)
            if ymin <= yfig <= ymax:
                self.trace_selected.emit(self.fig.axes.index(self.ax))

    def _event_to_fig_coords(self, event):
        inv = self.fig.transFigure.inverted()
        return inv.transform((event.x, event.y))

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
        position = event.time
        marker = self.ax.axvline(position, animated=True)
        self.markers[event_id] = marker
        self.markers[event_id].set(**kwargs)

    def set_marker_position(self, event):
        event_id = event.resource_id.uuid
        position = event.time
        marker = self.markers[event_id]
        if marker is not None:
            marker.set_xdata(position)

    def set_marker(self, event, **kwargs):
        event_id = event.resource_id.uuid
        marker = self.markers[event_id]
        if marker is not None:
            kwargs.pop("animated", None)  # marker's animated property must be always true to be drawn properly
            marker.set(**kwargs)

    def delete_marker(self, event):
        event_id = event.resource_id.uuid
        marker = self.markers[event_id]
        if marker is not None:
            self.ax.lines.remove(marker)
            self.markers.pop(event_id)

    def remove(self):
        self.fig.delaxes(self.ax)
        self.trace_selected.disconnect()
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

        # Animation related attrs.
        self.background = []
        self.animated = False
        self.size = (self.fig.bbox.width, self.fig.bbox.height)

        # Set TracePlot list
        self.trace_plots = []

        self.stream = None
        if stream is not None:
            self.set_stream(stream)

    def set_stream(self, stream):
        self.stream = stream
        # Clear canvas
        for axes in self.fig.axes:
            self.fig.delaxes(axes)
        # Plot stream traces
        self.trace_plots = []
        for i, trace in enumerate(self.stream.traces):
            self.trace_plots.append(TracePlot(self, trace, fig_nrows=len(stream), ax_pos=i))
        # Draw canvas
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
        for trace_idx in self.markers.keys():
            for event_id in self.markers[trace_idx].keys():
                marker = self.markers[trace_idx].get(event_id)
                self.fig.draw_artist(marker)
        self.canvas.blit(self.fig.bbox)

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
        self.fig.subplots_adjust(left=0.06, right=0.95, bottom=0.14,
                                 top=0.95, hspace=0.22)

    def showEvent(self, event):
        self.draw()

    def resizeEvent(self, event):
        self.draw()

