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

from PySide import QtCore
from PySide import QtGui
from PySide.phonon import Phonon
import numpy as np
import cStringIO
import scipy.io.wavfile as wavfile
import time

sample_rates = (2000, 4000, 6000, 8000, 10000, 16000)
bit_depths = ('int8', 'int16')


class PlayerToolBar(QtGui.QToolBar):
    """Allows the user to play a seismic signal.

    Attributes:
        data: Seismic data, numpy array type.
        data_fs: Sample rate of 'data', in Hz.
        fs: Sample rate used to play 'data', in Hz. Available values are
            2000, 4000, 6000, 8000, 10000 and 16000.
            Default: 2000 samples/sec.
        bd: Bit depth of 'data' samples once loaded. Available values
            are 'int8' and 'int16', i.e. 8 and 16 bits depth.
        repeat: Determines whether to replay or not.
            Default: False.
        connected: Indicates whether the media player is connected to an
            audio output or not.
        data_loaded: Indicates whether a seismic signal has been loaded
            onto the player or not.

    Signal:
        tick: Emits current time position in the stream currently being
            played at a given interval.
    """

    tick = QtCore.Signal(float)
    intervalChanged = QtCore.Signal(float, float)
    intervalSelected = QtCore.Signal(bool)

    def __init__(self, parent=None, data=None, data_fs=None, fs=2000,
                 bd='int16', repeat=False, tick_interval=200):
        if fs not in sample_rates:
            raise ValueError('Unsupported sampling rate: %s' % fs)
        if bd not in bit_depths:
            raise ValueError('Unsupported bit depth: %s' % bd)
        if tick_interval < 1:
            raise ValueError('tick_interval must be greater than zero.')
        super(PlayerToolBar, self).__init__(parent)
        self._audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self._mediaObject = Phonon.MediaObject(self)
        self._mediaObject.setTickInterval(tick_interval)
        self._mediaObject.aboutToFinish.connect(self.about_to_finish)
        self._mediaObject.finished.connect(self.finished)
        self._mediaObject.currentSourceChanged.connect(self.current_source_changed)
        self._mediaObject.tick.connect(self.on_tick)
        self._mediaObject.stateChanged.connect(self.state_changed)
        self.connected = False
        self.connect_path()
        self._buffer = QtCore.QBuffer()
        self.buffer_loaded = False
        self._start = 0
        self._end = np.inf
        self._interval_selected = False
        self.repeat = repeat
        self.fs = fs
        self.bd = bd
        if data is not None:
            self.load_data(data, data_fs)
        else:
            self.data = None
            self.data_fs = None
            self.data_loaded = False
        self._init_ui()

    def _init_ui(self):
        self.setEnabled(False)
        self.actionPlay = QtGui.QAction(self)
        self.actionPlay.setText("Play")
        self.actionPlay.setIcon(QtGui.QIcon.fromTheme("media-playback-start"))
        self.actionPlay.setEnabled(True)
        self.actionPause = QtGui.QAction(self)
        self.actionPause.setText("Pause")
        self.actionPause.setIcon(QtGui.QIcon.fromTheme("media-playback-pause"))
        self.actionPause.setEnabled(False)
        self.actionStop = QtGui.QAction(self)
        self.actionStop.setText("Stop")
        self.actionStop.setIcon(QtGui.QIcon.fromTheme("media-playback-stop"))
        self.actionStop.setEnabled(False)
        self.actionRepeat = QtGui.QAction(self)
        self.actionRepeat.setCheckable(True)
        self.actionRepeat.setText("Repeat")
        self.actionRepeat.setIcon(QtGui.QIcon.fromTheme("media-playlist-repeat"))
        self.addAction(self.actionPlay)
        self.addAction(self.actionPause)
        self.addAction(self.actionStop)
        self.addSeparator()
        self.addAction(self.actionRepeat)
        self.addSeparator()
        self.volumeSlider = Phonon.VolumeSlider(self)
        self.volumeSlider.setMaximumWidth(200)
        self.volumeSlider.setAudioOutput(self._audioOutput)
        self.addWidget(self.volumeSlider)
        self.addSeparator()
        self.labelStart = QtGui.QLabel(" Start:", self)
        self.tsbStart = QtGui.QTimeEdit(self)
        self.tsbStart.setDisplayFormat("hh 'h' mm 'm' ss.zzz 's'")
        self.tsbStart.setMinimumTime(QtCore.QTime().addSecs(0))
        self.labelEnd = QtGui.QLabel(" End:", self)
        self.tsbEnd = QtGui.QTimeEdit(self)
        self.tsbEnd.setDisplayFormat("hh 'h' mm 'm' ss.zzz 's'")
        self.labelPosition = QtGui.QLabel(" Position:", self)
        self.tsbPosition = QtGui.QTimeEdit(self)
        self.tsbPosition.setDisplayFormat("hh 'h' mm 'm' ss.zzz 's'")
        self.tsbPosition.setReadOnly(True)
        self.addWidget(self.labelStart)
        self.addWidget(self.tsbStart)
        self.addWidget(self.labelEnd)
        self.addWidget(self.tsbEnd)
        self.addWidget(self.labelPosition)
        self.addWidget(self.tsbPosition)
        # connect ui
        self.actionPlay.triggered.connect(self.on_play)
        self.actionStop.triggered.connect(self._mediaObject.stop)
        self.actionPause.triggered.connect(self._mediaObject.pause)
        self.actionRepeat.toggled.connect(self.toggle_repeat)
        self.tsbStart.timeChanged.connect(self.on_start_time_changed)
        self.tsbEnd.timeChanged.connect(self.on_end_time_changed)

    def current_source_changed(self, source):
        pass

    def about_to_finish(self):
        pass

    def finished(self):
        self._mediaObject.stop()
        if self.repeat:
            self.on_play()

    def toggle_repeat(self, value):
        if value != self.repeat:
            self.repeat = value

    def set_enabled(self, value):
        if self.data_loaded and self.connected:
            self.setEnabled(value)
        else:
            self.setEnabled(False)

    def on_play(self):
        if self._mediaObject.state() == Phonon.StoppedState:
            if not self.buffer_loaded:
                self._load_buffer()
            self._mediaObject.setCurrentSource(self._buffer)
        self._mediaObject.play()

    def load_data(self, data, data_fs):
        """Loads a seismic signal onto the player.

        Args:
            data: Seismic data, numpy array type.
            data_fs: Sample rate of loaded data.
        """
        self.data = (((data - data.mean()) / (max(data) - min(data))) *
                     np.iinfo(self.bd).max).astype(self.bd)
        self.data_fs = data_fs
        self._start = 0
        self._end = len(self.data)
        self.data_loaded = True
        self.toggle_interval_selected(False)
        # update ui
        self.tsbStart.setMinimumTime(QtCore.QTime().addMSecs(0))
        self.tsbEnd.setMaximumTime(QtCore.QTime().addMSecs(int(1000 *
                                                               len(self.data) /
                                                               self.data_fs)))
        self._update_qtimeedit_range()
        self.buffer_loaded = False
        self._load_buffer()

    def _load_buffer(self):
        if not self.data_loaded:
            raise UnboundLocalError("Data not initialized.")
        stream = cStringIO.StringIO()
        wavfile.write(stream, self.fs, self.data[self._start:self._end])
        if self._buffer.isOpen():
            self._buffer.close()
        self._buffer.setData(stream.read())
        self._buffer.open(QtCore.QBuffer.ReadOnly)
        self._mediaObject.clear()
        self._mediaObject.setCurrentSource(Phonon.MediaSource(self._buffer))
        self.buffer_loaded = True

    def set_limits(self, t_from, t_to):
        """Sets a time interval into loaded data to be played.

        Args:
            t_from: Start time point of the interval to be played, in seconds.
            t_to: End time point of the interval to be played, in seconds.
        """
        if not self.data_loaded:
            raise UnboundLocalError("Data not initialized.")
        t_from = int(max(0, t_from) * self.data_fs)
        t_to = int(min(len(self.data), t_to) * self.data_fs)
        if t_from > t_to:
            raise ValueError("t_to must be greater or equal than t_from")
        if (t_from, t_to) != (self._start, self._end):
            if t_from == t_to:
                self.toggle_interval_selected(False)
                self._start = 0
                self._end = len(self.data)
            else:
                self.toggle_interval_selected(True)
                self._start = t_from
                self._end = t_to
            self.buffer_loaded = False
            self.intervalChanged.emit(self._start / self.data_fs, self._end / self.data_fs)
            # update ui
            self._update_qtimeedit_range()

    def _update_qtimeedit_range(self):
        t_start = QtCore.QTime().addMSecs(int((self._start / self.data_fs) * 1000))
        t_end = QtCore.QTime().addMSecs(int((self._end / self.data_fs) * 1000))
        self.tsbStart.setTime(t_start)
        self.tsbEnd.setTime(t_end)

    def on_tick(self, value):
        if self.data_loaded and self.buffer_loaded:
            offset = ((self._start / self.data_fs) + (value / 1000.0) *
                      (self.fs / self.data_fs))
            self.tick.emit(offset)
            t = time.strftime('%X', time.gmtime(offset))
            self.tsbPosition.setTime(QtCore.QTime().addMSecs(int(offset * 1000)))

    def on_start_time_changed(self, value):
        t_from = int(max(0, (QtCore.QTime().msecsTo(value) / 1000.0) *
                         self.data_fs))
        if t_from != self._start:
            self._start = t_from
            self.tsbEnd.setMinimumTime(value)
            self.buffer_loaded = False
            self.toggle_interval_selected(True)
            self.intervalChanged.emit(self._start / self.data_fs, self._end / self.data_fs)

    def on_end_time_changed(self, value):
        t_to = int(min(len(self.data), (QtCore.QTime().msecsTo(value) /
                                        1000.0) * self.data_fs))
        if t_to != self._end:
            self._end = t_to
            self.tsbStart.setMaximumTime(value)
            self.buffer_loaded = False
            self.toggle_interval_selected(True)
            self.intervalChanged.emit(self._start / self.data_fs, self._end / self.data_fs)

    def state_changed(self, state):
        if state == Phonon.BufferingState:
            pass
        if state == Phonon.PlayingState:
            self.actionPlay.setEnabled(False)
            self.actionStop.setEnabled(True)
            self.actionPause.setEnabled(True)
            self.tsbStart.setEnabled(False)
            self.tsbEnd.setEnabled(False)
        elif state == Phonon.StoppedState:
            self.actionPlay.setEnabled(True)
            self.actionStop.setEnabled(False)
            self.actionPause.setEnabled(False)
            self.tsbStart.setEnabled(True)
            self.tsbEnd.setEnabled(True)
        elif state == Phonon.PausedState:
            self.actionPlay.setEnabled(True)
            self.actionStop.setEnabled(False)
            self.actionPause.setEnabled(False)
            self.tsbStart.setEnabled(False)
            self.tsbEnd.setEnabled(False)

    def connect_path(self):
        """Connect the player to an audio output."""
        if not self.connected:
            self._path = Phonon.createPath(self._mediaObject, self._audioOutput)
            self.connected = True

    def disconnect_path(self):
        """Disconnect the player from audio output and clear loaded data."""
        if self.connected:
            self._path.disconnectPath()
            self._mediaObject.clear()
            self.set_enabled(False)
            self.connected = False
            self.data_loaded = False
            self.buffer_loaded = False

    def toggle_interval_selected(self, value):
        """Activates/deactivates selection of a time interval."""
        if value != self._interval_selected:
            self._interval_selected = value
            self.buffer_loaded = False
            self.intervalSelected.emit(self._interval_selected)
            if not self._interval_selected:
                self._start = 0
                self._end = len(self.data)
            self._update_qtimeedit_range()

    def set_audio_format(self, fs=2000, bd='int16'):
        if fs not in sample_rates:
            raise ValueError('Unsupported sampling rate')
        if bd not in bit_depths:
            raise ValueError('Unsupported bit depth')
        if self.fs != fs or self.bd != bd:
            self.fs = fs
            self.bd = bd
            if self.data_loaded:
                self.load_data(self.data, self.data_fs)



