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
import matplotlib.pyplot as plt


class StreamViewerWidget(QtGui.QWidget):
    """Shows the entire signal and allows the user to navigate through it.

    Provides an scrollable selector over the entire signal.

    Attributes:
        xmin: Selector lower limit (measured in h-axis units).
        xmax: Selector upper limit (measured in h-axis units).
        step: Selector length (measured in h-axis units).
    """

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
        self.canvas.mpl_connect('button_press_event', self.onpress)
        self.canvas.mpl_connect('button_release_event', self.onrelease)

        # Animation related attrs.
        self.background = []
        self.animated = False
        self.size = (self.fig.bbox.width, self.fig.bbox.height)

        # Set the layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

        # Set Markers dict
        self.markers = {}

        self.stream = None
        if stream is not None:
            self.set_stream(stream)

    def set_stream(self, stream):
        self.stream = stream
        # Plot stream traces
        self.fig = self.stream.plot(fig=self.fig,
                                    equal_scale=False,
                                    handle=True,
                                    automerge=False)
        # Plot event markers
        self.markers = {}
        for trace_idx, trace in enumerate(self.stream):
            for event in trace.events:
                event_id = event.resource_id.uuid
                self.create_marker(trace_idx, event_id, event.time)
        # Draw canvas
        self.canvas.draw_idle()
        # self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        # self.draw_animate()

    def onpress(self, event):
        self.press_selector = event

    def onrelease(self, event):
        self.press_selector = None

    def draw(self):
        self.draw_animate()

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

