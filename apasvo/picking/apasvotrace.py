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
import obspy as op
import multiprocessing as mp
import itertools
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.event import Pick
from obspy.core.event import ResourceIdentifier
from obspy.core.event import CreationInfo
from obspy.core.event import WaveformStreamID
from obspy.core.event import Comment
from obspy.core.event import Catalog
from obspy.core.event import Event
import csv
import copy
import os
import uuid
import gc

from apasvo.picking import takanami
from apasvo.picking import envelope as env
from apasvo.utils.formats import rawfile
from apasvo.utils import collections
from apasvo.utils import clt

method_other = 'other'
method_takanami = 'Takanami'
method_stalta = 'STALTA'
method_stalta_takanami = 'STALTA+Takanami'
method_ampa = 'AMPA'
method_ampa_takanami = 'AMPA+Takanami'

ALLOWED_METHODS = (
    method_other,
    method_takanami,
    method_stalta,
    method_stalta_takanami,
    method_ampa,
    method_ampa_takanami
)

PHASE_VALUES = (
    "P",
    "S",
    "Other",
)

mode_manual = 'manual'
mode_automatic = 'automatic'

status_preliminary = 'preliminary'
status_reviewed = 'reviewed'
status_confirmed = 'confirmed'
status_rejected = 'rejected'
status_final = 'final'

DEFAULT_DTYPE = '=f8'  # Set the default datatype as 8 bits floating point, native ordered
DEFAULT_DELTA = 0.02


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
        status: Revision status of the event. Possible values are: 'preliminary',
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
             'time': record.starttime + event.time,
             'cf_value': event.cf_value,
             'name': event.name,
             'method': event.method,
             'mode': event.evaluation_mode,
             'status': event.evaluation_status,
             'comments': event.comments} for record in records
                                         for event in record.events]
    # Write data to csv
    writer = csv.DictWriter(fout, ['file_name', 'time', 'cf_value', 'name',
                                  'method', 'mode', 'status', 'comments'],
                            delimiter=delimiter, lineterminator=lineterminator)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


class ApasvoEvent(Pick):
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
            Default: 'preliminary'.
        n0_aic: Start time point of computed AIC values. The value is given in
            samples from the beginning of record.signal.
        aic: List of AIC values from n0_aic.
    """

    methods = (method_other, method_takanami, method_stalta,
               method_stalta_takanami, method_ampa, method_ampa_takanami)

    def __init__(self,
                 trace,
                 time,
                 name='',
                 comments='',
                 method=method_other,
                 phase_hint=None,
                 aic=None,
                 n0_aic=None,
                 *args, **kwargs):
        self.trace = trace
        if time < 0 or time >= len(self.trace.signal):
            raise ValueError("Event position must be a value between 0 and %d"
                             % len(self.trace.signal))
        self.stime = time
        self.name = name
        self.method = method
        self.aic = aic
        self.n0_aic = n0_aic
        phase_hint = phase_hint if phase_hint in PHASE_VALUES else PHASE_VALUES[0]
        super(ApasvoEvent, self).__init__(time=self.time,
                                          method_id=ResourceIdentifier(method),
                                          phase_hint=phase_hint,
                                          creation_info=CreationInfo(
                                              author=kwargs.get('author', ''),
                                              agency_id=kwargs.get('agency', ''),
                                              creation_time=UTCDateTime.now(),
                                          ),
                                          waveform_id=WaveformStreamID(
                                              network_code=self.trace.stats.get('network', ''),
                                              station_code=self.trace.stats.get('station', ''),
                                              location_code=self.trace.stats.get('location', ''),
                                              channel_code=self.trace.stats.get('channel', ''),
                                          ),
                                          *args,
                                          **kwargs)
        self.comments = comments

    @property
    def cf_value(self):
        if 0 <= self.stime < len(self.trace.cf):
            return self.trace.cf[self.stime]
        else:
            return np.nan

    def _samples_to_seconds(self, value):
        return self.trace.starttime + (self.trace.delta * value)

    def _seconds_to_samples(self, value):
        return int((value - self.trace.starttime) / self.trace.delta)

    def __setattr__(self, key, value):
        if key == 'stime':
            self.__dict__[key] = value
            self.__dict__['time'] = self._samples_to_seconds(value)
        elif key == 'time':
            self.__dict__[key] = value
            self.__dict__['stime'] = self._seconds_to_samples(value)
        elif key == 'comments':
            self.__dict__['comments'] = Comment(text=value)
        else:
            super(ApasvoEvent, self).__setattr__(key, value)

    def __getattribute__(self, item):
        if item == 'comments':
            return self.__dict__['comments'].text
        else:
            return super(ApasvoEvent, self).__getattribute__(item)

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
        i_to = int(min(len(self.trace.signal), self.n0_aic + len(self.aic)))
        # Create time sequence
        t = np.arange(i_from, i_to) / float(self.trace.fs)
        # Create figure
        fig, _ = pl.subplots(2, 1, sharex='all', num=num)
        fig.canvas.set_window_title(self.trace.label)
        fig.set_tight_layout(True)
        # Configure axes
        for ax in fig.axes:
            ax.cla()
            ax.grid(True, which='both')
            formatter = ticker.FuncFormatter(lambda x, pos: clt.float_secs_2_string_date(x, self.trace.starttime))
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, prune='lower'))
            ax.set_xlabel('Time (seconds)')
            pl.setp(ax.get_xticklabels(), visible=True)
        # Draw signal
        fig.axes[0].set_title('Signal Amplitude')
        fig.axes[0].set_ylabel('Amplitude')
        fig.axes[0].plot(t, self.trace.signal[i_from:i_to], color='black',
                         label='Signal')
        # Draw envelope
        if show_envelope:
            fig.axes[0].plot(t, env.envelope(self.trace.signal[i_from:i_to]),
                         color='r', label='Envelope')
            fig.axes[0].legend(loc=0, fontsize='small')
        # Draw AIC
        fig.axes[1].set_title('AIC')
        fig.axes[1].plot(t, self.aic)
        # Draw event
        for ax in fig.axes:
            vline = ax.axvline(self.stime / self.trace.fs, label="Event")
            vline.set(color='r', ls='--', lw=2)
        # Configure limits and draw legend
        for ax in fig.axes:
            ax.set_xlim(t[0], t[-1])
            ax.legend(loc=0, fontsize='small')
        return fig


class ApasvoTrace(op.Trace):
    """A seismic data trace.

    The class contains a seismic data trace.

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
    """

    def __init__(self, data=None, header=None, label='', description='', filename='', normalize=True, **kwargs):
        """Initializes a Record instance.

        Args:
            label: A string that identifies the seismic record. Default: ''.
            description: Additional comments.
        """
        # Cast data to default datatype
        if data is None:
            data = np.ndarray((0,), dtype=DEFAULT_DTYPE)
        super(ApasvoTrace, self).__init__(data, header)
        self.cf = np.array([], dtype=DEFAULT_DTYPE)
        if normalize:
            self.data = self.data - np.mean(self.data)
            #self.data = self.data/ np.max(np.abs(self.data))
        self.events = []
        self.label = label
        self.description = description
        self.filename = filename
        # Get an uuid for each trace
        self.uuid = unicode(uuid.uuid4())

    @property
    def fs(self):
        return 1. / self.stats.delta

    @property
    def delta(self):
        return self.stats.delta

    @property
    def signal(self):
        return self.data

    @property
    def starttime(self):
        return self.stats.starttime

    @property
    def endtime(self):
        return self.stats.endtime

    @property
    def short_name(self):
        return "{0} | {1}".format(os.path.basename(self.filename), self.id)

    @property
    def name(self):
        return "{0} | {1}".format(os.path.basename(self.filename), str(self))

    def detect(self, alg, threshold=None, peak_window=1.0,
               takanami=False, takanami_margin=5.0, action='append', debug=False, **kwargs):
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
            if method_name not in ApasvoEvent.methods:
                method_name = method_other
            events.append(ApasvoEvent(self, t, method=method_name,
                                      evaluation_mode=mode_automatic,
                                      evaluation_status=status_preliminary))
        # Refine arrival times
        if takanami:
            events = self.refine_events(events, takanami_margin=takanami_margin)
        # Update event list
        if action == 'append':
            self.events.extend(events)
        elif action == 'clear':
            self.events = events
        else:
            raise ValueError("%s is not a valid value for 'action'" % action)
        if debug:
            print "{} event(s) found so far for trace {}:".format(len(self.events), self.getId())
            for event in self.events:
                print event.time
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
            t_start = (event.stime / self.fs) - takanami_margin
            t_end = (event.stime / self.fs) + takanami_margin
            et, event.aic, event.n0_aic = taka.run(self.signal, self.fs,
                                                   t_start, t_end)
            event.stime = et
            # set event method
            if event.method == method_ampa:
                event.method = method_ampa_takanami
            elif event.method == method_stalta:
                event.method = method_stalta_takanami
            else:
                event.method = method_takanami
        return events

    def save_cf(self, fname, fmt=rawfile.format_text,
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
        if fmt == 'binary':
            fout_handler = rawfile.BinFile(fname, dtype=dtype,
                                           byteorder=byteorder)
        else:
            fout_handler = rawfile.TextFile(fname, dtype=dtype,
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
        t = np.arange(i_from, i_to) / float(self.fs)
        # Create figure
        nplots = show_x + show_cf + show_specgram
        fig, _ = pl.subplots(nplots, 1, sharex='all', num=num)
        fig.canvas.set_window_title(self.label)
        fig.set_tight_layout(True)
        # Configure axes
        for ax in fig.axes:
            ax.cla()
            ax.grid(True, which='both')
            formatter = ticker.FuncFormatter(lambda x, pos: clt.float_secs_2_string_date(x, self.starttime))
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, prune='lower'))
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
            #fig.axes[ax_idx].plot(t, signal_norm, color='black',
                                  #label='Signal')
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
                arrival_time = event.stime / self.fs
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

    def add_event_from_copy(self, event):
        event = copy.copy(event)
        event.trace = self
        event.aic = None
        event.n0_aic = None
        self.events.append(event)

def _detect(parameters):
    alg = parameters[0]
    trace_list = parameters[1]
    kwargs = parameters[2]
    for trace in trace_list:
        trace.detect(alg, **kwargs)
    return trace_list

class ApasvoStream(op.Stream):
    """
    A list of multiple ApasvoTrace objects
    """

    def __init__(self, traces, description='', filename='', **kwargs):
        super(ApasvoStream, self).__init__(traces)
        self.description = description
        self.filename = filename

    def detect(self, alg, trace_list=None, allow_multiprocessing=True, **kwargs):
        """
        """
        trace_list = self.traces if trace_list is None else trace_list[:]
        n_traces = len(trace_list)
        if allow_multiprocessing and n_traces > 1:
            processes = min(mp.cpu_count(), n_traces)
            p = mp.Pool(processes=processes)
            processed_traces = p.map(_detect, itertools.izip(itertools.repeat(alg),
                                               collections.chunkify(trace_list, n_traces / processes),
                                               itertools.repeat(kwargs)))
            processed_traces = collections.flatten_list(processed_traces)
            # Update existing traces w. new events and cf from  processed events
            for trace, processed_trace in zip(trace_list, processed_traces):
                new_events = [event for event in processed_trace.events if event not in trace.events]
                for event in new_events:
                    trace.add_event_from_copy(event)
                trace.cf = processed_trace.cf[:]
            # Cleanup
            del processed_traces
            del trace_list
            p.close()
            p.join()
            gc.collect(2)
        else:
            _detect((alg, trace_list, kwargs))

    def export_picks(self, filename, trace_list=None, format="NLLOC_OBS", debug=False, **kwargs):
        """
        """
        trace_list = self.traces if trace_list is None else trace_list
        event_list = []
        for trace in trace_list:
            event_list.extend([Event(picks=[pick]) for pick in trace.events])
        # Export to desired format
        if format == 'NLLOC_OBS':
            basename, ext = os.path.splitext(filename)
            for event in event_list:
                ts = event.picks[0].time.strftime("%Y%m%d%H%M%S%f")
                event_filename = "%s_%s%s" % (basename, ts, ext)
                if debug:
                    print "Generating event file {}".format(event_filename)
                event.write(event_filename, format=format)
        else:
            event_catalog = Catalog(event_list)
            if debug:
                print "Generating event file {}".format(filename)
            event_catalog.write(filename, format=format, **kwargs)

def read(filename,
         format=None,
         dtype='float64',
         byteorder='native',
         description='',
         normalize=True,
         *args, **kwargs):
    """
    Read signal files into an ApasvoStream object
    :param filename:
    :param format:
    :param file_dtype:
    :param file_byteorder:
    :param description:
    :param args:
    :param kwargs:
    :return:
    """
    # Try to read using obspy core functionality
    try:
        traces = [ApasvoTrace(copy.deepcopy(trace.data), copy.deepcopy(trace.stats), filename=filename, normalize=normalize) \
                  for trace in op.read(filename, format=format, *args, **kwargs).traces]
    # Otherwise try to read as a binary or text file
    except Exception as e:
        fhandler = rawfile.get_file_handler(filename,
                                            format=format,
                                            dtype=dtype,
                                            byteorder=byteorder)
        trace = ApasvoTrace(fhandler.read().astype(DEFAULT_DTYPE, casting='safe'), filename=filename)
        sample_fs = kwargs.get('fs')
        trace.stats.delta = DEFAULT_DELTA if sample_fs is None else 1. / sample_fs
        traces = [trace]
    # Convert Obspy traces to apasvo traces
    return ApasvoStream(traces, description=description, filename=filename)
