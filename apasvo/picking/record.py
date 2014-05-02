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

import numpy as np
import csv
import os
import datetime

from apasvo.picking import takanami
from apasvo.picking import envelope as env
from apasvo.utils.formats import rawfile
from apasvo.utils import clt

method_other = 'other'
method_takanami = 'Takanami'
method_stalta = 'STALTA'
method_stalta_takanami = 'STALTA+Takanami'
method_ampa = 'AMPA'
method_ampa_takanami = 'AMPA+Takanami'

mode_manual = 'manual'
mode_automatic = 'automatic'
mode_undefined = 'undefined'

status_reported = 'reported'
status_revised = 'revised'
status_confirmed = 'confirmed'
status_rejected = 'rejected'
status_undefined = 'undefined'


def generate_csv(records, fout, delimiter=',', lineterminator='\n'):
    """Generates a Comma Separated Value (CSV) resume file from a list of
    Record objects.

    The function stores into a file a summary table of the events found
    for a given list of records. The table has the following fields:
        file_name: Name of the file (absolute path) that stores the data
            signal where the event was found.
        time: Event arrival time, in seconds from the beginning of the signal.
        cf_value: Characteristic function value at the event arrival time.
        name: An arbitrary string that identifies the event.
        method: A string indicating the algorithm used to find the event.
            Possible values are: 'STA-LTA', 'STA-LTA+Takanami', 'AMPA',
            'AMPA+Takanami' and 'other'.
        mode: Event picking mode. Possible values are: 'manual', 'automatic'
            and 'undefined'.
        status: Revision status of the event. Possible values are: 'reported',
            'revised', 'confirmed', 'rejected' and 'undefined'.
        comments: Additional comments.

    Args:
        records: A list of record objects.
        fout: Output file object.
        delimiter: A delimiter character that separates fields/columns.
            Default character is ','.
        lineterminator: A delimiter character that separates records/rows.
    """
    # Extract data from records
    rows = [{'file_name': record.filename,
             'time': str(datetime.timedelta(seconds=event.time / record.fs)),
             'cf_value': event.cf_value,
             'name': event.name,
             'method': event.method,
             'mode': event.mode,
             'status': event.status,
             'comments': event.comments} for record in records
                                         for event in record.events]
    # Write data to csv
    writer = csv.DictWriter(fout, ['file_name', 'time', 'cf_value', 'name',
                                  'method', 'mode', 'status', 'comments'],
                            delimiter=delimiter, lineterminator=lineterminator)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


class Event(object):
    """A seismic event found in a Record instance.

    This class stores several attributes used to describe a possible event
    found in a seismic signal, as well as data results from the computation
    of Takanami algorithm in order to refine the arrival time of the event.

    Attributes:
        record: Record instance where the event was found.
        time: Event arrival time, given in samples from the beginning of
            record.signal.
        cf_value: Characteristic function value at the event arrival time.
        name: An arbitrary string that identifies the event.
            Default: ''.
        comments: Additional comments.
            Default: ''.
        method: A string indicating the algorithm used to find the event.
            Possible values are: 'STALTA', 'STALTA+Takanami', 'AMPA',
            'AMPA+Takanami' and 'other'.
            Default: 'other'.
        mode: Event picking mode. Possible values are: 'manual', 'automatic'
            and 'undefined'.
            Default: 'automatic'.
        status: Revision status of the event. Possible values are: 'reported',
            'revised', 'confirmed', 'rejected' and 'undefined'.
            Default: 'reported'.
        n0_aic: Start time point of computed AIC values. The value is given in
            samples from the beginning of record.signal.
        aic: List of AIC values from n0_aic.
    """

    methods = (method_other, method_takanami, method_stalta,
               method_stalta_takanami, method_ampa, method_ampa_takanami)
    modes = (mode_manual, mode_automatic, mode_undefined)
    statuses = (status_reported, status_revised, status_confirmed,
                status_rejected, status_undefined)

    def __init__(self, record, time, name='', comments='',
                 method=method_other, mode=mode_automatic, status=status_reported,
                 aic=None, n0_aic=None, **kwargs):
        super(Event, self).__init__()
        self.record = record
        if time < 0 or time >= len(self.record.signal):
            raise ValueError("Event position must be a value between 0 and %d"
                             % len(self.record.signal))
        self.time = time
        self.name = name
        self.comments = comments
        self.method = method
        if mode not in self.modes:
            mode = mode_undefined
        self.mode = mode
        if status not in self.statuses:
            status = status_undefined
        self.status = status
        self.aic = aic
        self.n0_aic = n0_aic

    @property
    def cf_value(self):
        if 0 <= self.time < len(self.record.cf):
            return self.record.cf[self.time]
        else:
            return np.nan

    def plot_aic(self, show_envelope=True, num=None, **kwargs):
        """Plots AIC values for a given event object.

        Draws a figure with two axes: the first one plots magnitude and
        envelope of 'self.signal' and the second one plots AIC values computed
        after applying Takanami AR method to 'event'. Plotted data goes from
        'event.n0_aic' to 'event.n0_aic + len(event.aic)'.

        Args:
            show_envelope: Boolean value to specify whether to plot the
                envelope of 'signal' or not. This function will be drawn
                preferably on the first axis together with amplitude of
                'signal'.
                Default: True.
            num: Identifier of the returned MatplotLib figure, integer type.
                Default None, which means an identifier value will be
                automatically generated.

        Returns:
            fig: A MatplotLib Figure instance.
        """
        if self.aic is None or self.n0_aic is None:
            raise ValueError("Event doesn't have AIC data to plot")

        # Lazy matplotlib import
        import matplotlib.pyplot as pl
        from matplotlib import ticker

        # Set limits
        i_from = int(max(0, self.n0_aic))
        i_to = int(min(len(self.record.signal), self.n0_aic + len(self.aic)))
        # Create time sequence
        t = np.arange(i_from, i_to) / self.record.fs
        # Create figure
        fig, _ = pl.subplots(2, 1, sharex='all', num=num)
        fig.canvas.set_window_title(self.record.label)
        fig.set_tight_layout(True)
        # Configure axes
        for ax in fig.axes:
            ax.cla()
            ax.grid(True, which='both')
            formatter = ticker.FuncFormatter(lambda x, pos: clt.float_secs_2_string_date(x))
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=8))
            ax.set_xlabel('Time (seconds)')
            pl.setp(ax.get_xticklabels(), visible=True)
        # Draw signal
        fig.axes[0].set_title('Signal Amplitude')
        fig.axes[0].set_ylabel('Amplitude')
        fig.axes[0].plot(t, self.record.signal[i_from:i_to], color='black',
                         label='Signal')
        # Draw envelope
        if show_envelope:
            fig.axes[0].plot(t, env.envelope(self.record.signal[i_from:i_to]),
                         color='r', label='Envelope')
            fig.axes[0].legend(loc=0, fontsize='small')
        # Draw AIC
        fig.axes[1].set_title('AIC')
        fig.axes[1].plot(t, self.aic)
        # Draw event
        for ax in fig.axes:
            vline = ax.axvline(self.time / self.record.fs, label="Event")
            vline.set(color='r', ls='--', lw=2)
        # Configure limits and draw legend
        for ax in fig.axes:
            ax.set_xlim(t[0], t[-1])
            ax.legend(loc=0, fontsize='small')
        return fig


class Record(object):
    """A seismic data record.

    The class contains a seismic data trace. Provides methods that allows

    Attributes:
        signal: Seismic data, numpy array type.
        fs: Sample rate in Hz.
        cf: Characteristic function, numpy array type, from the beginning
            of signal.
        events: A list of events.
        label: A string that identifies the stored seismic data.
            Default: ''.
        description: Additional comments.
            Default: ''.
        filename: Name of the file (absolute path) where data is stored.
    """

    def __init__(self, fileobj, fs, label='', description='', fmt='',
                 dtype=rawfile.datatype_float64,
                 byteorder=rawfile.byteorder_native, **kwargs):
        """Initializes a Record instance.

        Args:
            fileobj: A file (binary or plain text) storing seismic data.
            fs: Sample rate in Hz.
            label: A string that identifies the seismic record. Default: ''.
            description: Additional comments.
            fmt: A string indicating fileobj's format. Possible values are
                'binary', 'text' or ''. Default value is ''.
            dtype: Data-type of the data stored in fileobj. Default value
                is 'float64'.
            byteorder: Byte-order of the data stored in fileobj.
                Valid values are: 'little-endian', 'big-endian' and 'native'.
                Default: 'native'.
        """
        super(Record, self).__init__()
        if isinstance(fileobj, file):
            self.filename = fileobj.name
        else:
            self.filename = fileobj
        fhandler = rawfile.get_file_handler(fileobj, fmt=fmt, dtype=dtype,
                                            byteorder=byteorder)
        self.signal = fhandler.read().astype(rawfile.datatype_float64, casting='safe')
        self.fs = fs
        self.cf = np.array([], dtype=rawfile.datatype_float64)
        self.events = []
        if label == '':
            _, rname = os.path.split(self.filename)
            label, _ = os.path.splitext(rname)
        self.label = label
        self.description = description

    def detect(self, alg, threshold=None, peak_window=1.0,
               takanami=False, takanami_margin=5.0, action='append', **kwargs):
        """Computes a picking algorithm over self.signal.

        Args:
            alg: A detection/picking algorithm object, e. g. a
                picking.ampa.Ampa or picking.stalta.StaLta instance.
            threshold: Local maxima found in the characteristic function above
                this value will be returned by the function as possible events
                (detection mode).
                If threshold is None, the function will return only the global
                maximum (picking mode).
                Default value is None.
            peak_window: How many seconds on each side of a point of the
                characteristic function to use for the comparison to consider
                the point to be a local maximum.
                If 'threshold' is None, this parameter has no effect.
                Default value is 1 s.
            takanami: A boolean parameter to specify whether Takanami AR method
                will be applied over results or not.
                Default: False, Takanami wont be applied over results.
            takanami_margin: How many seconds on each side of an event time to
                use for the application of Takanami method.
                If 'takanami' is False, this parameter has no effect.
                Default: 5.0 seconds.
            action: Two valid choices: 'append' and 'clear'. 'append' adds the
                events found to the end of the list of events, while 'clear'
                removes the existing events of the list.
                Default: 'append'.

        Returns:
            events: A resulting list of Event objects.
        """
        et, self.cf = alg.run(self.signal, self.fs, threshold=threshold,
                                peak_window=peak_window)
        # Build event list
        events = []
        for t in et:
            # set method name
            method_name = alg.__class__.__name__.upper()
            if method_name not in Event.methods:
                method_name = method_other
            events.append(Event(self, t, method=method_name,
                                     mode=mode_automatic, status=status_reported))
        # Refine arrival times
        if takanami:
            events = self.refine_events(events, takanami_margin)
        # Update event list
        if action == 'append':
            self.events.extend(events)
        elif action == 'clear':
            self.events = events
        else:
            raise ValueError("%s is not a valid value for 'action'" % action)
        return self.events

    def sort_events(self, key='time', reverse=False):
        """Sort event list.

        Args:
            key: Name of the attribute of Event class to use as sorting key.
                Default: 'time'.
            reverse: Determines whether to sort in reverse order or not.
                Default: False.

        Returns:
            events: Sorted event list.
        """
        if key == 'aic':
            raise ValueError("Sorting not allowed using key 'aic'")
        self.events = sorted(self.events,
                             key=lambda e: e.__dict__.get(key, None),
                             reverse=reverse)
        return self.events

    def refine_events(self, events, t_start=None, t_end=None, takanami_margin=5.0):
        """Computes Takanami AR method over self.events.

        Args:
            takanami_margin: How many seconds on each side of an event time to
                use for the application of Takanami method.
                If 'takanami' is False, this parameter has no effect.
                Default: 5.0 seconds.

        Returns:
            events: A resulting list of Event objects.
        """
        taka = takanami.Takanami()
        for event in events:
            t_start = (event.time / self.fs) - takanami_margin
            t_end = (event.time / self.fs) + takanami_margin
            et, event.aic, event.n0_aic = taka.run(self.signal, self.fs,
                                                   t_start, t_end)
            event.time = et
            # set event method
            if event.method == method_ampa:
                event.method = method_ampa_takanami
            elif event.method == method_stalta:
                event.method = method_stalta_takanami
            else:
                event.method = method_takanami
        return events

    def save_cf(self, fname, fmt=rawfile.format_binary,
                dtype=rawfile.datatype_float64,
                byteorder=rawfile.byteorder_native):
        """Saves characteristic function in a file.

        Args:
            fname: Output file name.
            fmt: A string indicating the format to store the CF.
                Possible values are: 'binary' or 'text'.
                Default value: 'binary'.
            dtype: Data-type to represent characteristic function values.
                Default: 'float64'.
            byteorder: Byte-order to store characteristic function values.
                Valid values are: 'little-endian', 'big-endian' or 'native'.
                Default: 'native'.
        """
        if fmt == 'text':
            fout_handler = rawfile.TextFile(fname, dtype=dtype,
                                            byteorder=byteorder)
        else:
            fout_handler = rawfile.BinFile(fname, dtype=dtype,
                                           byteorder=byteorder)
        fout_handler.write(self.cf, header="Sample rate: %g Hz." % self.fs)

    def plot_signal(self, t_start=0.0, t_end=np.inf, show_events=True,
                    show_x=True, show_cf=True, show_specgram=True,
                    show_envelope=True, threshold=None, num=None, **kwargs):
        """Plots record data.

        Draws a figure containing several plots for data stored and computed
        by a Record object: magnitude, envelope and spectrogram plots for
        self.signal, as well as characteristic function if calculated.

        Args:
            t_start: Start time of the plotted data segment, in seconds.
                Default: 0.0, that is the beginning of 'signal'.
            t_end: End time of the plotted data segment, in seconds.
                Default: numpy.inf, that is the end of 'signal'
            show_events: Boolean value to specify whether to plot
                event arrival times or not. Arrival times will be
                indicated by using a vertical line.
                Default: True.
            show_x: Boolean value to specify whether to plot the
                magnitude value of 'signal' or not. This function
                will be drawn preferably on the first axis.
                Default: True.
            show_cf: Boolean value to specify whether to plot the
                characteristic function or not. This function
                will be drawn preferably on the second axis.
                Default: True.
            show_specgram: Boolean value to specify whether to plot the
                spectrogram of 'signal' or not. It will be drawn preferably
                on the third axis.
                Default: True.
            show_envelope: Boolean value to specify whether to plot the
                envelope of 'signal' or not. This function will be drawn
                preferably on the first axis together with amplitude of
                'signal'.
                Default: True.
            threshold: Boolean value to specify whether to plot threshold
                or not. Threshold will be drawn as an horizontal dashed line
                together with characteristic function.
                Default: True.
            num: Identifier of the returned MatplotLib figure, integer type.
                Default None, which means an identifier value will be
                automatically generated.

        Returns:
            fig: A MatplotLib Figure instance.
        """
        # Lazy matplotlib import
        import matplotlib.pyplot as pl
        from matplotlib import ticker

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
            formatter = ticker.FuncFormatter(lambda x, pos: clt.float_secs_2_string_date(x))
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(ticker.MaxNLocator(prune='lower'))
            ax.set_xlabel('Time (seconds)')
            pl.setp(ax.get_xticklabels(), visible=True)
        # Draw axes
        ax_idx = 0
        # Draw signal
        if show_x:
            fig.axes[ax_idx].set_title("Signal Amplitude (%gHz)" % self.fs)
            fig.axes[ax_idx].set_ylabel('Amplitude')
            fig.axes[ax_idx].plot(t, self.signal[i_from:i_to], color='black',
                                  label='Signal')
            # Draw signal envelope
            if show_envelope:
                fig.axes[ax_idx].plot(t, env.envelope(self.signal[i_from:i_to]),
                                  color='r', label='Envelope')
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
                arrival_time = event.time / self.fs
                for ax in fig.axes:
                    xmin, xmax = ax.get_xlim()
                    if arrival_time > xmin and arrival_time < xmax:
                        vline = ax.axvline(arrival_time, label="Event")
                        vline.set(color='r', ls='--', lw=2)
                        ax.legend(loc=0, fontsize='small')
        # Configure limits and draw legend
        for ax in fig.axes:
            ax.set_xlim(t[0], t[-1])
        return fig


class RecordFactory(object):
    """Builder class to create Record objects.

    Attributes:
        fs: Sample rate in Hz.
        dtype: Data-type of the data to read.
        byteorder: Byte-order of the data to read.
        max_record_length: Maximum signal length allowed, in seconds.
            Currently this attribute has no effect.
            Default value: 604800.0 seconds (1 week).
    """

    def __init__(self, max_segment_length=24 * 7 * 3600, fs=50.0,
                 dtype='float64', byteorder='native', **kwargs):
        self.fs = fs
        self.dtype = dtype
        self.byteorder = byteorder
        self.max_record_length = (max_segment_length * fs)

    def create_record(self, fileobj, **kwargs):
        """Creates a Record object.

        Args:
            fileobj: A file (binary or plain text) storing seismic data.

        Returns:
            out: Created Record object.
        """
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

#     def on_notify(self, msg):
#         """"""
#         pass
