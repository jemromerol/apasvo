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

import numpy as np
from scipy import signal
import csv
import os
import matplotlib.pyplot as pl
from matplotlib.ticker import FuncFormatter
import datetime

from takanami import Takanami
from utils.formats import rawfile


def envelope(x):
    return np.abs(signal.hilbert(x))


def generate_csv(records, out, delimiter='\t', lineterminator='\n'):
    # Extract data from records
    rows = [{'file_name': record.filename,
             'time': str(datetime.timedelta(seconds=event.time)),
             'cf_value': event.cf_value,
             'name': event.name,
             'method': event.method,
             'mode': event.mode,
             'state': event.state,
             'comments': event.comments} for record in records
                                         for event in record.events]
    # Write data to csv
    writer = csv.DictWriter(out, ['file_name', 'time', 'cf_value', 'name', 'method', 'mode', 'state', 'comments'],
                            delimiter=delimiter, lineterminator=lineterminator)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


class Event(object):

    methods = ['other', 'STA-LTA', 'STA-LTA+Takanami', 'AMPA', 'AMPA+Takanami']
    modes = ['manual', 'automatic', 'undefined']
    states = ['reported', 'revised', 'confirmed', 'rejected', 'undefined']

    def __init__(self, time, cf_value, name='', comments='', method='other',
                 mode='automatic', state='reported', aic=None, n0_aic=None, **kwargs):
        super(Event, self).__init__()
        self.time = time
        self.cf_value = cf_value
        self.name = name
        self.comments = comments
        self.method = method
        if mode not in self.modes:
            mode = 'undefined'
        self.mode = mode
        if state not in self.states:
            state = 'undefined'
        self.state = state
        self.aic = aic
        self.n0_aic = n0_aic


class Record(object):

    def __init__(self, fileobj, fs, label='', description='', fmt='', dtype='float64', byteorder='native', **kwargs):
        super(Record, self).__init__()
        if isinstance(fileobj, file):
            self.filename = fileobj.name
        else:
            self.filename = fileobj
        fhandler = rawfile.get_file_handler(fileobj, fmt=fmt, dtype=dtype, byteorder=byteorder)
        self.signal = fhandler.read()
        self.fs = fs
        self.cf = np.array([])
        self.events = []
        if label == '':
            _, rname = os.path.split(self.filename)
            label, _ = os.path.splitext(rname)
        self.label = label
        self.description = description

    def detect(self, alg, threshold=None, peak_checking=1.0, sort='vd',
               takanami=False, takanami_margin=5.0, **kwargs):
        et, self.cf = alg.run(self.signal, self.fs, threshold=threshold,
                                peak_window=peak_checking)
        # Build event list
        self.events = []
        for t in et:
            self.events.append(Event(t / self.fs, self.cf[t], method=alg.name,
                                     mode='automatic', state='reported'))
        # Sort results
        key = 'cf_value' if sort[0] == 'v' else 'time'
        reverse = True if sort[1] == 'd' else False
        self.sort_events(key, reverse)
        # Refine
        if takanami:
            self._refine_events(takanami_margin)
        return self.events

    def sort_events(self, key='time', reverse=False):
        if key == 'aic':
            raise ValueError("Sorting not allowed using key 'aic'")
        self.events = sorted(self.events, key=lambda e: e.__dict__.get(key, None), reverse=reverse)

    def _refine_events(self, takanami_margin=5.0):
        taka = Takanami()
        for event in self.events:
            t_start = event.time - takanami_margin
            t_end = event.time + takanami_margin
            et, event.aic, event.n0_aic = taka.run(self.signal, self.fs,
                                                   t_start, t_end)
            event.time = et / self.fs
            event.cf_value = self.cf[et]
        return self.events

    def save_cf(self, fname, fmt='binary', dtype='float64', byteorder='native'):
        fout_handler = rawfile.TextFile(fname, dtype=dtype, byteorder=byteorder) if fmt == 'text' else rawfile.BinFile(fname, dtype=dtype, byteorder=byteorder)
        fout_handler.write(self.cf)

    def plot_signal(self, t_start=0.0, t_end=np.inf, show_events=True,
                    show_x=True, show_cf=True, show_specgram=True,
                    show_envelope=True, threshold=None, num=None, **kwargs):
        # Set limits
        i_from = int(max(0.0, t_start * self.fs))
        if show_cf:
            i_to = int(min(len(self.cf), t_end * self.fs))
        else:
            i_to = int(min(len(self.signal), t_end * self.fs))
        # Create time sequence
        t = np.arange(i_from, i_to) / self.fs
        # Create figure
        nplots = show_x + show_cf + show_specgram
        fig, _ = pl.subplots(nplots, 1, sharex='all', num=num)
        fig.canvas.set_window_title(self.label)
        fig.set_tight_layout(True)
        # Configure axes
        for ax in fig.axes:
            ax.cla()
            ax.grid(True, which='both')
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f' % x))
            ax.set_xlabel('Time (seconds)')
            pl.setp(ax.get_xticklabels(), visible=True)
        # Draw axes
        ax_idx = 0
        # Draw signal
        if show_x:
            fig.axes[ax_idx].set_title("Signal Amplitude (%gHz)" % self.fs)
            fig.axes[ax_idx].set_ylabel('Amplitude')
            fig.axes[ax_idx].plot(t, self.signal[i_from:i_to], color='b', label='Signal')
            # Draw signal envelope
            if show_envelope:
                fig.axes[ax_idx].plot(t, envelope(self.signal[i_from:i_to]),
                                  color='g', label='Envelope')
                fig.axes[ax_idx].legend(loc=0, fontsize='small')
            ax_idx += 1
        # Draw Characteristic function
        if show_cf:
            fig.axes[ax_idx].set_title('Characteristic Function')
            fig.axes[ax_idx].plot(t, self.cf[i_from:i_to])
            # Draw threshold
            if threshold:
                hline = fig.axes[ax_idx].axhline(threshold, label="Threshold")
                hline.set(color='b', ls='--', lw=2, alpha=0.8)
                fig.axes[ax_idx].legend(loc=0, fontsize='small')
            ax_idx += 1
        # Draw spectrogram
        if show_specgram:
            fig.axes[ax_idx].set_title('Spectrogram')
            fig.axes[ax_idx].set_ylabel('Frequency (Hz)')
            fig.axes[ax_idx].specgram(self.signal[i_from:i_to], Fs=self.fs,
                                  xextent=(i_from / self.fs, i_to / self.fs))
            ax_idx += 1
        # Draw event markers
        if show_events:
            for event in self.events:
                for ax in fig.axes:
                    xmin, xmax = ax.get_xlim()
                    if event.time > xmin and event.time < xmax:
                        vline = ax.axvline(event.time, label="Event")
                        vline.set(color='r', ls='--', lw=2)
                        ax.legend(loc=0, fontsize='small')
        # Configure limits and draw legend
        for ax in fig.axes:
            ax.set_xlim(t[0], t[-1])
        return fig

    def plot_aic(self, event, show_envelope=True, num=None, **kwargs):
        # Set limits
        i_from = int(max(0, event.n0_aic))
        i_to = int(min(len(self.signal), event.n0_aic + len(event.aic)))
        # Create time sequence
        t = np.arange(i_from, i_to) / self.fs
        # Create figure
        fig, _ = pl.subplots(2, 1, sharex='all', num=num)
        fig.canvas.set_window_title(self.label)
        fig.set_tight_layout(True)
        # Configure axes
        for ax in fig.axes:
            ax.cla()
            ax.grid(True, which='both')
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.0f' % x))
            ax.set_xlabel('Time (seconds)')
            pl.setp(ax.get_xticklabels(), visible=True)
        # Draw signal
        fig.axes[0].set_title('Signal Amplitude')
        fig.axes[0].set_ylabel('Amplitude')
        fig.axes[0].plot(t, self.signal[i_from:i_to], color='b', label='Signal')
        # Draw envelope
        if show_envelope:
            fig.axes[0].plot(t, envelope(self.signal[i_from:i_to]),
                         color='g', label='Envelope')
            fig.axes[0].legend(loc=0, fontsize='small')
        # Draw AIC
        fig.axes[1].set_title('AIC')
        fig.axes[1].plot(t, event.aic)
        # Draw event
        for ax in fig.axes:
            vline = ax.axvline(event.time, label="Event")
            vline.set(color='r', ls='--', lw=2)
        # Configure limits and draw legend
        for ax in fig.axes:
            ax.set_xlim(t[0], t[-1])
            ax.legend(loc=0, fontsize='small')
        return fig


class RecordFactory(object):

    def __init__(self, max_segment_length=24*7*3600, fs=50.0, dtype='float64', byteorder='native',
                 notif=None, **kwargs):
        self.fs = fs
        self.dtype = dtype
        self.byteorder = byteorder
        self.max_record_length = (max_segment_length * fs)
        self.notif = notif

    def create_record(self, fileobj, **kwargs):
#         segment_n = np.ceil(utils.getSize(fileobj) / self.max_record_length)
#         if segment_n > 1:
#             fhandler = utils.get_file_handler(fileobj, dtype=self.dtype, byteorder=self.byteorder)
#             self.on_notify("File %s is too long, it will be divided into %i parts up to %g seconds each\n"
#                            % (fhandler.filename, segment_n, self.max_record_length / self.fs))
#             basename, ext = os.path.splitext(fhandler.filename)
#             fileno = 0
#             records = []
#             for segment in fhandler.read_in_blocks(self.max_record_length):
#                 filename_out = "%s%02.0i%s" % (basename, fileno, ext)
#                 fout_handler = utils.TextFile(filename_out, self.dtype, self.byteorder) if isinstance(fhandler, utils.TextFile) else utils.BinFile(filename_out, self.dtype, self.byteorder)
#                 fileno += 1
#                 fout_handler.write(segment)
#                 self.on_notify("%s generated.\n" % fout_handler.filename)
#                 records.append(fout_handler.filename, self.fs,
#                                       dtype=self.dtype, byteorder=self.byteorder,
#                                       **kwargs)
#             return records
#         else:
        return Record(fileobj, self.fs, dtype=self.dtype, byteorder=self.byteorder,
                      **kwargs)

    def on_notify(self, msg):
        pass
