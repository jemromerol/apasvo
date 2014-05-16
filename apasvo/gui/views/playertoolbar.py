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

from PySide import QtCore
from PySide import QtGui
from PySide.phonon import Phonon
from apasvo.gui.views.generated import qrc_icons
from scipy import interpolate
import numpy as np
import cStringIO
import scipy.io.wavfile as wavfile


bit_depths = {'16 bits, PCM': 'int16', '32 bits, float': 'float32'}
MINIMUM_REAL_FREQ = 4000.0
DEFAULT_REAL_FREQ = 100.0
DEFAULT_BIT_DEPTH = 'float32'


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
    playingStateSelected = QtCore.Signal()
    stoppedStateSelected = QtCore.Signal()
    pausedStateSelected = QtCore.Signal()
    playingStateChanged = QtCore.Signal(bool)

    def __init__(self, parent=None, data=None, data_fs=None, sample_freq=None,
                 bd='float32', tick_interval=200):
        if bd not in bit_depths.values():
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
        self._raw_data = None
        self.bd = bd

        if sample_freq is not None:
            self.sample_freq = float(sample_freq)
        else:
            self.sample_freq = None

        self._real_freq = None

        if data is not None:
            self.load_data(data, data_fs)
        else:
            self.data = None
            self._data_fs = None
            self.data_loaded = False
        self._init_ui()

    def _init_ui(self):
        self.setEnabled(False)
        self.actionPlay = QtGui.QAction(self)
        self.actionPlay.setText("Play")
        self.actionPlay.setIcon(QtGui.QIcon(":/play.png"))
        self.actionPlay.setEnabled(True)
        self.actionPause = QtGui.QAction(self)
        self.actionPause.setText("Pause")
        self.actionPause.setIcon(QtGui.QIcon(":/pause.png"))
        self.actionPause.setEnabled(False)
        self.actionStop = QtGui.QAction(self)
        self.actionStop.setText("Stop")
        self.actionStop.setIcon(QtGui.QIcon(":/stop.png"))
        self.actionStop.setEnabled(False)
        self.addAction(self.actionPlay)
        self.addAction(self.actionPause)
        self.addAction(self.actionStop)
        self.addSeparator()
        self.volumeSlider = Phonon.VolumeSlider(self)
        self.volumeSlider.setMaximumWidth(200)
        self.volumeSlider.setAudioOutput(self._audioOutput)
        self.addWidget(self.volumeSlider)
        self.addSeparator()
        self.labelStart = QtGui.QLabel(" Start:", self)
        self.tsbStart = QtGui.QTimeEdit(self)
        self.tsbStart.setDisplayFormat("hh 'h' mm 'm' ss.zzz 's'")
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
        self.actionStop.triggered.connect(self.on_stop)
        self.actionPause.triggered.connect(self._mediaObject.pause)
        self.tsbStart.timeChanged.connect(self.on_start_time_changed)
        self.tsbEnd.timeChanged.connect(self.on_end_time_changed)

    @property
    def t_end(self):
        if self.data_loaded:
            return self._end / self._data_fs
        return None

    @property
    def t_start(self):
        if self.data_loaded:
            return self._start / self._data_fs
        return None

    def current_source_changed(self, source):
        pass

    def about_to_finish(self):
        pass

    def finished(self):
        self._mediaObject.stop()
        self.playingStateChanged.emit(False)

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
        if self._mediaObject.state() != Phonon.PausedState:
            self.tick.emit(self.t_start)
        self.playingStateChanged.emit(True)
        self._mediaObject.play()

    def on_stop(self):
        self._mediaObject.stop()
        self.playingStateChanged.emit(False)

    def load_data(self, data, data_fs):
        """Loads a seismic signal onto the player.

        Args:
            data: Seismic data, numpy array type.
            data_fs: Sample rate of loaded data.
        """
        if len(data) == 0:
            return
        self._raw_data = data
        self._data_fs = data_fs
        self._interpolator = interpolate.InterpolatedUnivariateSpline(np.arange(len(self._raw_data)),
                                                                      self._raw_data, k=1)

        # set playing rate
        if self.sample_freq is None:
            self.sample_freq = self._data_fs
        if self.sample_freq < MINIMUM_REAL_FREQ:
            self._real_freq = MINIMUM_REAL_FREQ
            n_samples = int((len(self._raw_data) - 1) * self._real_freq / self.sample_freq) + 1
            self.data = self._interpolator(np.linspace(0, len(self._raw_data) - 1, n_samples))
        else:
            self._real_freq = self.sample_freq
            self.data = self._raw_data

        # normalize and cast to specified datatype
        self.data = (self.data - self.data.mean()) / (np.max(self.data) - np.min(self.data))
        if np.dtype(self.bd).kind == 'i':
            max_value = np.iinfo(self.bd).max
            self.data = (self.data * max_value).astype(self.bd, copy=False)
        elif np.dtype(self.bd).kind == 'f':
            self.data = self.data.astype(self.bd, copy=False)
        else:
            raise TypeError("Datatype not supported")

        self._start = 0
        self._end = len(self._raw_data) - 1
        self.data_loaded = True
        # update ui
        self.tsbStart.setMinimumTime(QtCore.QTime().addMSecs(0))
        self.tsbEnd.setMaximumTime(QtCore.QTime().addMSecs(int(1000 * self.t_end)))
        self._update_qtimeedit_range()
        self.toggle_interval_selected(False)
        self.buffer_loaded = False
        self._load_buffer()

    def _load_buffer(self):
        if not self.data_loaded:
            raise UnboundLocalError("Data not initialized.")
        stream = cStringIO.StringIO()
        start = int(self._start * self._real_freq / self.sample_freq)
        end = min(len(self.data) - 1, int(self._end * self._real_freq / self.sample_freq))
        wavfile.write(stream, self._real_freq, self.data[start:end + 1])
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
        t_from_in_samples = int(max(0, t_from) * self._data_fs)
        t_to_in_samples = int(min(len(self._raw_data), t_to) * self._data_fs)
        if not 0 <= t_from_in_samples <= t_to_in_samples <= len(self._raw_data):
            raise ValueError("t_to must be greater or equal than t_from")
        if t_from_in_samples != t_to_in_samples:
            if (t_from_in_samples, t_to_in_samples) != (self._start, self._end):
                self.toggle_interval_selected(True)
                self._start = t_from_in_samples
                self._end = t_to_in_samples
                self.buffer_loaded = False
                self.intervalChanged.emit(t_from, t_to)
                # update ui
                self._update_qtimeedit_range()

    def _update_qtimeedit_range(self):
        t_start = QtCore.QTime().addMSecs(int(self.t_start * 1000))
        t_end = QtCore.QTime().addMSecs(int(self.t_end * 1000))
        # block valuechanged signals in order to avoid their propagation
        self.tsbStart.blockSignals(True)
        self.tsbEnd.blockSignals(True)

        self.tsbStart.setTime(t_start)
        self.tsbEnd.setMinimumTime(t_start)
        self.tsbEnd.setTime(t_end)
        self.tsbStart.setMaximumTime(t_end)

        self.tsbStart.blockSignals(False)
        self.tsbEnd.blockSignals(False)

    def on_tick(self, value):
        if self.data_loaded and self.buffer_loaded:
            value_in_samples = (value / 1000.0) * self._real_freq
            offset = self.t_start + int(value_in_samples * self.sample_freq / self._real_freq) / self._data_fs
            self.tsbPosition.setTime(QtCore.QTime().addMSecs(int(offset * 1000)))
            self.tick.emit(offset)

    def on_start_time_changed(self, value):
        t_from = max(0, QtCore.QTime().msecsTo(value) / 1000.0)
        t_from_in_samples = int(t_from * self._data_fs)
        if t_from_in_samples != self._start:
            self._start = t_from_in_samples
            self.tsbEnd.setMinimumTime(value)
            self.buffer_loaded = False
            self.toggle_interval_selected(True)
            self.intervalChanged.emit(t_from, self.t_end)

    def on_end_time_changed(self, value):
        t_to = min(len(self._raw_data), QtCore.QTime().msecsTo(value) / 1000.0)
        t_to_in_samples = int(t_to * self._data_fs)
        if t_to_in_samples != self._end:
            self._end = t_to_in_samples
            self.tsbStart.setMaximumTime(value)
            self.buffer_loaded = False
            self.toggle_interval_selected(True)
            self.intervalChanged.emit(self.t_start, t_to)

    def state_changed(self, state):
        if state == Phonon.BufferingState:
            pass
        if state == Phonon.PlayingState:
            self.actionPlay.setEnabled(False)
            self.actionStop.setEnabled(True)
            self.actionPause.setEnabled(True)
            self.tsbStart.setEnabled(False)
            self.tsbEnd.setEnabled(False)
            self.playingStateSelected.emit()
        elif state == Phonon.StoppedState:
            self.actionPlay.setEnabled(True)
            self.actionStop.setEnabled(False)
            self.actionPause.setEnabled(False)
            self.tsbStart.setEnabled(True)
            self.tsbEnd.setEnabled(True)
            self.stoppedStateSelected.emit()
        elif state == Phonon.PausedState:
            self.actionPlay.setEnabled(True)
            self.actionStop.setEnabled(True)
            self.actionPause.setEnabled(False)
            self.tsbStart.setEnabled(False)
            self.tsbEnd.setEnabled(False)
            self.pausedStateSelected.emit()

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
                self._end = len(self._raw_data)
            self._update_qtimeedit_range()

    def set_audio_format(self, sample_freq=500.0, bd='float32'):
        if bd not in bit_depths.values():
            raise ValueError('Unsupported bit depth')
        if self.sample_freq != sample_freq or self.bd != bd:
            self.sample_freq = sample_freq
            self.bd = bd
            if self.data_loaded:
                self.load_data(self._raw_data, self._data_fs)



