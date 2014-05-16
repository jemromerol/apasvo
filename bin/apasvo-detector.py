#!/usr/bin/python2.7
# encoding: utf-8
'''Earthquake Detector
A tool to detect/pick earthquakes on seismic signals.

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

import argparse
import sys
import os
import datetime

from apasvo._version import __version__
from apasvo.utils import clt
from apasvo.utils import parse
from apasvo.utils import collections
from apasvo.picking import stalta
from apasvo.picking import ampa
from apasvo.picking import record as rc


def draw_events_table(record, method):
    """Draws into a CLI table a summary of the events found for a given seismic
    record.

    Args:
        record: A picking.Record object
        method: Algorithm used, e.g. AMPA or STA-LTA.
    """
    sys.stdout.write("%i possible events found in %s:\n" %
                     (len(record.events), record.filename))
    sys.stdout.flush()
    et = ["%s" % datetime.timedelta(seconds=e.time / record.fs)
          for e in record.events]
    cf_val = [e.cf_value for e in record.events]
    if len(et) > 0:
        sys.stdout.write("\n%s\n\n" %
                         clt.Table(clt.Column("No.", range(1, len(et) + 1)),
                                     clt.Column("Time(s)", et, fmt='%s'),
                                     clt.Column("%s CF Value" % method.upper(),
                                                cf_val)))
        sys.stdout.flush()


def draw_results(records, method):
    """Draws into a CLI table a summary of the events found for a list of
    seismic records.

    Args:
        records: A list of picking.Record objects
        method: Algorithm used, e.g. AMPA.
    """
    # Extract data from records
    data = [{'file_name':record.filename,
             'time':str(datetime.timedelta(seconds=event.time / record.fs)),
             'cf_value': event.cf_value} for record in records
                                            for event in record.events]
    sys.stdout.write("Summary of events:\n")
    sys.stdout.write("\n%s\n\n" %
                     clt.Table(clt.Column("File Name",
                                          [e['file_name'] for e in data],
                                          fmt='%s'),
                                 clt.Column("Time(s)",
                                            [e['time'] for e in data], fmt="%s"),
                                 clt.Column("%s CF Value" % method.upper(),
                                            [e['cf_value'] for e in data])))
    sys.stdout.flush()


def print_settings(args):
    """Print settings to stdout.

    Args:
        args: Command-line input arguments.
    """
    sys.stdout.write("\nGeneral settings:\n")
    sys.stdout.write("%30s: %s\n" % ("Signal frequency(Hz)",
                                   args.fs))
    if args.threshold:
        sys.stdout.write("%30s: %s\n" % ("Threshold",
                                       args.threshold))
    sys.stdout.write("%30s: %s\n" % ("Peak checking(s)",
                                   args.peak_checking))
    sys.stdout.write("%30s: %s\n" % ("Algorithm used",
                                   args.method.upper()))
    sys.stdout.write("%30s: %s\n" % ("Takanami",
                                   args.takanami))
    sys.stdout.write("%30s: %s\n" % ("Takanami margin",
                                   args.takanami_margin))
    if args.method == 'ampa':
        sys.stdout.write("\nAMPA settings:\n")
        sys.stdout.write("%30s: %s\n" % ("Window length(s)",
                                       args.window))
        sys.stdout.write("%30s: %s\n" % ("Window overlap",
                                       args.step))
        sys.stdout.write("%30s: %s\n" % ("Noise threshold",
                                       args.noise_thr))
        sys.stdout.write("%30s: %s\n" % ("Length of the filters used(s)",
                                       args.L))
        sys.stdout.write("%30s: %s\n" % ("Negative response coefficient",
                                       args.L_coef))
        sys.stdout.write("%30s: %s\n" % ("Coefficient U",
                                       args.U))
        sys.stdout.write("\nAMPA filter bank settings:\n")
        sys.stdout.write("%30s: %s\n" % ("Start frequency(Hz)",
                                       args.f_start))
        sys.stdout.write("%30s: %s\n" % ("End frequency(Hz)",
                                       args.f_end))
        sys.stdout.write("%30s: %s\n" % ("Subband bandwidth(Hz)",
                                       args.bandwidth))
        sys.stdout.write("%30s: %s\n" % ("Subband overlap(Hz)",
                                       args.overlap))
    if args.method == 'stalta':
        sys.stdout.write("\nSTA-LTA settings:\n")
        sys.stdout.write("%30s: %s\n" % ("STA window length(s)",
                                       args.sta_length))
        sys.stdout.write("%30s: %s\n" % ("LTA window length(s)",
                                       args.lta_length))
    sys.stdout.write("\n")
    sys.stdout.flush()


class Analysis(object):
    """An abstract class to detect/pick earthquakes on seismic data.
    """

    _cf_dir = './cf_data'
    _sort_keys = {'va': ('cf_value', False), 'vd': ('cf_value', True),
                  'ta': ('time', False), 'td': ('time', True)}

    def run(self, FILEIN, csv=None, cf=False, **kwargs):
        """Event/picking detection on a given set of seismic signals.

        Reads a list of command-line input arguments, performs event analysis
        over a given list of seismic data inputs and generates a summary of
        results.
        Analysis can be performed in two ways: supervised or unsupervised mode.
        In supervised mode the function graphs each of the candidate events
        found and asks the user whether to accept them or not, whereas in
        unsupervised mode the function just computes results without receiving
        any feedback from users.

        Args:
            FILEIN: A list of binary or text file objects containing seismic
                data.
            csv: Determines whether to save a summary of results to a CSV
                file or not. Default value is None, meaning no CSV summary
                will be saved.
            cf: Determines whether to save generated characteristic function
                to a file (binary or text format) or not. Default value is
                False.
        """
        # Extract method name from kwargs
        method = kwargs.get('method', 'ampa')
        takanami = kwargs.get('takanami', False)
        # Create a list of records from input files
        factory = rc.RecordFactory(notif=clt.print_msg, **kwargs)
        factory.on_notify = clt.print_msg
        records = []
        for f in FILEIN:
            records.append(factory.create_record(f, method=method))
        records = collections.flatten_list(records)
        # Configure method
        self.on_notify('Configuring %s method... ' % method.upper())
        if method == 'stalta':
            alg = stalta.StaLta(**kwargs)
        else:
            alg = ampa.Ampa(**kwargs)
        self.on_notify("Done\n")
        # Run analysis
        self._do_analysis(records, alg, **kwargs)

        # Show results
        draw_results(records, method=method)

        # Generate reports
        if csv:
            self.on_notify("Generating CSV report in %s... " % csv.name)
            rc.generate_csv(records, csv)
            self.on_notify("Done\n")

        # Save cf
        if cf:
            for record in records:
                # Create a new directory to store CFs
                cf_path = os.path.abspath(self._cf_dir)
                if not os.path.exists(cf_path):
                    os.makedirs(cf_path)
                # Generate cf filenames
                bname, rname = os.path.splitext(os.path.basename(os.path.abspath(record.filename)))
                fname = os.path.join(cf_path, "%s.cf%s" % (bname, rname))
                self.on_notify("Saving CF for input file %s in %s... " %
                               (record.filename, fname))
                record.save_cf(fname, fmt=kwargs.get('cff', 'binary'),
                               dtype=kwargs.get('cfd', 'float64'),
                               byteorder=kwargs.get('cfb', 'native'))
                self.on_notify("Done\n")

    def _do_analysis(self, records, alg, supervised=False, **kwargs):
        raise NotImplementedError

    def _supervise_events(self, record, takanami=True, show_len=5.0,
                          show_cf=False, show_specgram=False,
                          show_envelope=False,
                          show_all=False, **kwargs):
        raise NotImplementedError

    def on_notify(self, msg):
        pass


class Detector(Analysis):
    """A class to perform event detection on seismic data.

    Takes a list of command line arguments and finds all those possible events
    whose characteristic function value is over a given threshold value for
    each input signal.
    """

    def _do_analysis(self, records, alg, supervised=False, sort=None, **kwargs):
        # Extract method name from kwargs
        method = kwargs.get('method', 'ampa')
        if supervised:
            import matplotlib.pyplot as pl
            pl.ion()
        for record in records:
            self.on_notify("Processing %s... " % record.filename)
            record.detect(alg, **kwargs)
            self.on_notify("Done\n")
            # Sort results
            if sort:
                key, reverse = self._sort_keys.get(sort, ('cf_value', True))
                record.sort_events(key, reverse)
            draw_events_table(record, method)
            if supervised:
                last_response = self._supervise_events(record, **kwargs)
                if last_response == "quit":
                    break
                elif last_response == "continue & don't ask again":
                    supervised = False
                    pl.close('all')
        if supervised:
            pl.ioff()
            pl.close('all')

    def _supervise_events(self, record, takanami=True, show_len=5.0,
                          show_cf=False, show_specgram=False,
                          show_envelope=False,
                          show_all=False, **kwargs):
        # Define Q&A for each mode
        detect_q = "Accept this event?"
        detect_a = ["&yes", "&no", "&accept all",
                    "&discard all", "&continue & don't ask again", "&quit"]
        detect_da = "yes"
        # Set default answer
        response = detect_da

        show_cf = True if show_all else show_cf
        show_specgram = True if show_all else show_specgram
        show_envelope = True if show_all else show_envelope

        accepted_events = []
        for i in xrange(len(record.events)):
            event = record.events[i]
            self.on_notify("Showing event no. %i of %i\n" %
                             (i + 1, len(record.events)))
            record.plot_signal(t_start=(event.time / record.fs) - show_len,
                               t_end=(event.time / record.fs) + show_len,
                               num=1,
                               show_cf=show_cf,
                               show_specgram=show_specgram,
                               show_envelope=show_envelope,
                               **kwargs)
            if takanami:
                event.plot_aic(num=2, show_envelope=show_envelope)
            # Query user and process its response
            response = clt.query_custom_answers(detect_q, detect_a,
                                                  default=detect_da)
            if response == "yes":
                accepted_events.append(i)
            elif (response == "accept all" or
                  response == "continue & don't ask again"):
                accepted_events.extend(range(i, len(record.events)))
                break
            elif response == "discard all" or response == "quit":
                break
        # Remove discarded events
        record.events = [record.events[i] for i in accepted_events]
        # Return last response
        return response


class Picker(Analysis):
    """A class to perform event picking on seismic data.

    Takes a list of command line input arguments and finds the global maximum
    of the characteristic function for each seismic input signal.
    """

    def _do_analysis(self, records, alg, supervised=False, **kwargs):
        # Extract method name from kwargs
        method = kwargs.get('method', 'ampa')
        if supervised:
            import matplotlib.pyplot as pl
            pl.ion()
        for record in records:
            self.on_notify("Processing %s... " % record.filename)
            if supervised:
                record.detect(alg, threshold=0.0, **kwargs)
                self.on_notify("Done\n")
                # Sort events
                key, reverse = self._sort_keys.get('vd', ('cf_value', True))
                record.sort_events(key, reverse)
                draw_events_table(record, method)
                last_response = self._supervise_events(record, **kwargs)
                if last_response == 'quit':
                    break
                elif last_response == 'all':
                    supervised = False
                    pl.close('all')
            else:
                record.detect(alg, **kwargs)
                self.on_notify("Done\n")
                draw_events_table(record, method)
        if supervised:
            pl.ioff()
            pl.close('all')

    def _supervise_events(self, record, takanami=True, show_len=5.0,
                          show_cf=False, show_specgram=False,
                          show_envelope=False,
                          show_all=False, **kwargs):
        # Define Q&A for each mode
        pick_q = "Accept this event?"
        pick_a = ["&yes", "&no", "&all", "&quit"]
        pick_da = "yes"
        # Set default answer
        response = pick_da

        show_cf = True if show_all else show_cf
        show_specgram = True if show_all else show_specgram
        show_envelope = True if show_all else show_envelope

        accepted_events = []
        for i in xrange(len(record.events)):
            event = record.events[i]
            self.on_notify("Showing event no. %i of %i\n" %
                             (i + 1, len(record.events)))
            record.plot_signal(t_start=event.time - show_len,
                               t_end=event.time + show_len,
                               num=1,
                               show_cf=show_cf,
                               show_specgram=show_specgram,
                               show_envelope=show_envelope)
            if takanami:
                event.plot_aic(num=2, show_envelope=show_envelope)
            # Query user and process its response
            response = clt.query_custom_answers(pick_q, pick_a,
                                                  default=pick_da)
            if response == "yes" or response == 'all':
                accepted_events.append(i)
                break
            elif response == "quit":
                break
        # Remove discarded events
        record.events = [record.events[i] for i in accepted_events]
        # Return last response
        return response


def analysis(**kwargs):
    """Performs event analysis/picking over a set of seismic signals.

    Performs event detection if parameter 'threshold' is not None, otherwise
    performs event picking.
    """
    if 'threshold' in kwargs:
        task = Detector()
    else:
        task = Picker()
    task.on_notify = clt.print_msg
    task.run(**kwargs)


def main(argv=None):
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = __import__('__main__').__doc__.split("\n")[0]
    program_version = "v%s" % __version__
    program_version_message = '%%(prog)s %s' % program_version
    program_description = '''
    %s %s

    A tool to perform event detection/picking over seismic signals.

    Analysis can be performed in two ways: supervised or unsupervised mode.
    In supervised mode the function graphs each of the candidate events
    found and asks the user whether to accept them or not, whereas in
    unsupervised mode the function just computes results without receiving
    any feedback from users.


    Created by Jose Emilio Romero Lopez.
    Copyright 2013. All rights reserved.

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

    ''' % (program_name, program_version)
    program_examples = '''
    Examples of use:

    \033[1m>> python apasvo-apasvo-detector.py meq01.bin meq02.bin -f 100 --takanami\033[0m

    Given two seismic signals, 'meq01.bin' and 'meq02.bin', sample rate 100 Hz,
    performs event picking by using AMPA method (default settings) together with
    Takanami method for arrival time refining.

    Saves results summary to 'output.csv'.

    \033[1m>> python apasvo-detector.py meq01.txt --csv example.out -m stalta --lta 60 --takanami -s --show-all\033[0m

    Let 'meq01.txt' a text file containing seismic data, performs event picking
    with the following settings:

        Sample rate: 50 Hz. (Default value).
        Picking Algorithm: STA-LTA.
            STA window length: 5.0 seconds. (Default value).
            LTA window length: 60.0 seconds.
        Apply Takanami AR method on results.

    Works on supervised mode, showing characteristic function, envelope
    function and espectrogram for each possible event.
    Saves results summary to 'example.out'

    \033[1m>> python apasvo-detector.py meq01.bin --cf -t 1.5 --ampa-filters 50.0 25.0 12.5 6.25  --ampa-noise-threshold 75 -s --show-cf\033[0m

    Let 'meq01.bin' a binary file containing seismic data, detects seismic
    events whose characteristic function value is over 1.5.
    Event detection uses the following settings:

        Detection Algorithm: AMPA.
            Filter lengths: 50.0 25.0 12.5 6.25 (in seconds).
            Noise threshold percentile: 75

    Works on supervised mode, showing characteristic function for each possible
    event.
    Saves results summary to 'output.csv'.
    Saves characteristic function to './cf_data/meq01.cf.bin'.

    \033[1m>> python apasvo-detector.py meq*.bin --csv example.out --cf --cff text @settings.txt\033[0m

    Performs event picking on all files matching 'meq*.bin' and takes some
    settings from a text file named 'settings.txt'.
    Saves results summary to 'example.out'.
    Saves characteristic functions to 'cf_data' folder, plain text format.

    The following settings are used:

        Picking Algorithm: AMPA.
            Sliding window length: 200.0 seconds.
            Sliding window step: 100.0 seconds. (50 % overlap).
            Filter lengths: 50.0, 20.0, 10.0, 6.0, 3.0 (in seconds).
            Noise threshold percentile: 75
            Frequency range: 4-25 Hz.

    So, the following is the content of 'settings.txt':

    >> cat settings.txt
    -m ampa
    --ampa-window 200.0
    --ampa-step 100.0
    --ampa-filters 50.0 20.0 10.0 6.0 3.0
    --ampa-noise-threshold 75
    --ampa-f-start 4.0
    --ampa-f-end 25.0
    '''

    try:
        # Setup argument parser
        parser = parse.CustomArgumentParser(description=program_description,
                                            epilog=program_examples,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                fromfile_prefix_chars='@')
        parser.set_defaults(func=analysis)
        parser.add_argument('-V', '--version', action='version',
                            version=program_version_message)
        parser.add_argument("FILEIN", nargs='+',
                            action=parse.GlobInputFilenames,
                            metavar='file',
                            help='''
    Binary or text file containing a seismic-like signal.
        ''')
        parser.add_argument("--csv", type=argparse.FileType('w'),
                            default="output.csv",
                            metavar='<file>',
                            help='''
    Output CSV summary file. Default: 'output.csv'.
        ''')
        parser.add_argument("-f", "--frequency", type=parse.positive_int,
                            default=50.0,
                            dest='fs',
                            metavar='<arg>',
                            help='''
    Sample rate in Hz. Default: 50 Hz
        ''')
        parser.add_argument("-m", "--method",
                            choices=['ampa', 'stalta'],
                            default='ampa',
                            help='''
    Available event detection/picking algorithms. Default: 'ampa'.
        ''')
        parser.add_argument("-t", "--threshold",
                            type=parse.positive_float,
                            metavar='<arg>',
                            help='''
    Local maxima in the characteristic function over this value will
    be considered as possible events (detection mode).
    If no threshold parameter is provided, the application takes only the
    global maximum of the characteristic function (picking mode).
        ''')
        parser.add_argument("--peak-window",
                            type=parse.positive_float,
                            default=1.0,
                            dest='peak_checking',
                            metavar='<arg>',
                            help='''
    How many seconds on each side of a point of the characteristic
    function to use for the comparison to consider the point to be
    a local maximum. If no threshold is provided, this parameter has
    no effect. Default value is 1 s.
        ''')
        parser.add_argument("--sort", choices=['td', 'ta', 'vd', 'va'],
                            default='vd',
                            help='''
    Specifies how to sort results. Choices are time descending/ascending
    and characteristic function value descending/ascending.
    Default value is 'vd', meaning value descending.
        ''')
        parser.add_argument("--datatype",
                            choices=['int16', 'int32', 'int64', 'float16', 'float32', 'float64'],
                            default='float64',
                            dest='dtype',
                            help='''
    Data-type of input data. Default value is float64, meaning double-precision
    floating point format.
        ''')
        parser.add_argument("--byteorder",
                            choices=['little-endian', 'big-endian', 'native'],
                            default='native',
                            help='''
    If the input files are in binary format this will be the byte-order
    of the selected datatype. Default choice is hardware native.
        ''')
    # Characteristic function arguments
        cf_options = parser.add_argument_group("Characteristic Function settings")
        cf_options.add_argument("--cf", action="store_true", default=False,
                            help='''
    Enables saving computed characteristic functions to file. Generated files
    will be saved to 'cf_data' folder, which will be created if not exists yet.
    E.g. given input files 'meq1.bin' and 'meq2.bin', saves their
    characteristic functions to './cf_data/meq1.cf.bin' and
    './cf_data/meq2.cf.bin'
        ''')
        cf_options.add_argument("--cff", choices=["binary", "text"],
                            default="binary",
                            help='''
    Characteristic function output file format.
    Default value is 'binary'.
        ''')
        cf_options.add_argument("--cfd", choices=['int16', 'int32', 'int64', 'float16', 'float32', 'float64'],
                            default='float64',
                            help='''
    Data-type of characteristic function saved data.
    Default value is 'float64', meaning double-precision floating point data..
        ''')
        cf_options.add_argument("--cfe", choices=['little-endian', 'big-endian', 'native'],
                            default='native',
                            help='''
    Endianness of characteristic function saved data.
    Default value is hardware native.
        ''')
        # STA-LTA arguments
        sta_lta_options = parser.add_argument_group("STA-LTA settings")
        sta_lta_options.add_argument("--sta",
                                     type=parse.positive_float,
                                     dest='sta_length',
                                     default=5.0,
                                     metavar='<arg>',
                                     help='''
    Length of STA window (in seconds) when using STA-LTA method.
    Default value is 5 seconds.
        ''')
        sta_lta_options.add_argument("--lta",
                                     type=parse.positive_float,
                                     dest='lta_length',
                                     default=100.0,
                                     metavar='<arg>',
                                     help='''
    Length of LTA window (in seconds) when using STA-LTA method.
    Default value is 100 seconds.
        ''')
        # AMPA arguments
        ampa_options = parser.add_argument_group("AMPA settings")
        ampa_options.add_argument("--ampa-window",
                                  type=parse.positive_float,
                                  dest='window',
                                  default=100.0,
                                  metavar='<arg>',
                                  help='''
    Sliding window length (in seconds) when using AMPA method.
    Typically this value should be close to the expected length
    of the events sought.
    Default: 100 seconds.
        ''')
        ampa_options.add_argument("--ampa-step",
                                  type=parse.positive_float,
                                  dest='step',
                                  default=50.0,
                                  metavar='<arg>',
                                  help='''
    Step length in seconds when using AMPA method.
    Default: 50 seconds.
        ''')
        ampa_options.add_argument("--ampa-filters",
                                  type=parse.positive_float,
                                  dest='L',
                                  default=[30.0, 20.0, 10.0, 5.0, 2.5],
                                  nargs='+',
                                  metavar='<arg>',
                                  help='''
    A list of filter lengths (in seconds) used by AMPA
    at the enhancement filter stage.
    The length of a filter is related to the duration of the detected
    events. An enhancement filter for long duration events can negate
    short duration events and vice versa. Combining several filters of
    different length the algorithm achieves to deal with this issue.
    Default values are 30.0, 20.0, 10.0, 5.0 and 2.5 seconds.
        ''')
        ampa_options.add_argument("--ampa-response-penalty",
                                  type=float,
                                  dest='L_coef',
                                  default=3.0,
                                  metavar='<arg>',
                                  help='''
    Penalty factor that minimizes response to emerging or impulsive noise
    of the set of filters applied at the enhancement stage.
    Default: 3.0.
        ''')
        ampa_options.add_argument("--ampa-noise-threshold",
                                  type=parse.percentile,
                                  dest='noise_thr',
                                  default=90.0,
                                  metavar='<arg>',
                                  help='''
    Percentile of the amplitude of the envelope that measures the noise
    reduction level for each band at noise reduction stage.
    Default: 90.
        ''')
        ampa_options.add_argument("--ampa-f-start",
                                  type=parse.positive_float,
                                  dest='f_start',
                                  default=2.0,
                                  metavar='<arg>',
                                  help='''
    Start frequency of the filter bank applied at the adaptive multi-band
    processing stage.
    Default: 2.0 Hz.
        ''')
        ampa_options.add_argument("--ampa-f-end",
                                  type=parse.positive_float,
                                  dest='f_end',
                                  default=12.0,
                                  metavar='<arg>',
                                  help='''
    End frequency of the filter bank applied at the adaptive multi-band
    processing stage.
    Default: 12.0 Hz.
        ''')
        ampa_options.add_argument("--ampa-bandwidth",
                                  type=parse.positive_float,
                                  dest='bandwidth',
                                  default=3.0,
                                  metavar='<arg>',
                                  help='''
    Channel bandwidth of the filter bank applied at the adaptive multi-band
    processing stage.
    Default: 3.0 Hz.
        ''')
        ampa_options.add_argument("--ampa-overlap",
                                  type=parse.positive_float,
                                  dest='overlap',
                                  default=1.0,
                                  metavar='<arg>',
                                  help='''
    Overlap between channels of the filter bank applied at the adaptive
    multi-band processing stage.
    Default: 1.0 Hz.
        ''')
        ampa_options.add_argument("--ampa-U",
                                  type=float,
                                  dest='U',
                                  default=12.0,
                                  metavar='<arg>',
                                  help='''
    A parameter used at the end of the enhancement filter stage to avoid
    logarithm of zero and to shift the characteristic function to zero.
    Given y(n) the product of the outputs of the different filters used
    at the end of the enhancement stage, the characteristic function is
    then calculated as:

        cf(n) = U + log10(y(n) + 10 ** (-U))

    Default: 12.0.
        ''')
        # Takanami arguments
        takanami_options = parser.add_argument_group("Takanami settings")
        takanami_options.add_argument("--takanami",
                                 action='store_true',
                                 default=False,
                                 help='''
    Specifies whether to use Takanami AR method to refine results or not.
        ''')

        takanami_options.add_argument("--takanami-len",
                                 type=parse.positive_float,
                                 dest='takanami_margin',
                                 default=5.0,
                                 metavar='<arg>',
                                 help='''
    Given a possible event time point, this parameter specifies the length
    of an interval centered at that point where to perform Takanami AR
    refining method. I.e. let 't' a possible arrival time and 'w' the value of
    the parameter, the application will perform Takanami AR method in
    [t - w, t + w].
    Default: 5.0 seconds.
        ''')

        # Create arguments for the supervised mode
        supervised_options = parser.add_argument_group("Supervised mode")
        supervised_options.add_argument("-s", "--supervised",
                                        action="store_true", default=False,
                                        help='''
    Enables supervised mode. In supervised mode the application graphs
    each of the candidate events found and asks the user whether to accept
    them or not.
        ''')
        supervised_options.add_argument("--show-cf",
                                        action="store_true", default=False,
                                        help='''
    Plots characteristic function in supervised mode.
        ''')
        supervised_options.add_argument("--show-specgram",
                                        action="store_true", default=False,
                                        help='''
    Plots spectrogram in supervised mode.
        ''')
        supervised_options.add_argument("--show-envelope",
                                        action="store_true", default=False,
                                        help='''
    Plots signal envelope in supervised mode. The function will be drawn
    together with signal amplitude.
        ''')
        supervised_options.add_argument("--show-all",
                                        action='store_true', default=False,
                                        help='''
    Equivalent to: --show-cf --show_envelope --show-specgram.
        ''')
        supervised_options.add_argument("--show-len",
                                        type=parse.positive_float,
                                        default=30.0,
                                        metavar='<arg>',
                                        help='''
    Specifies how many seconds will be displayed at most before and after
    of a possible event. I.e. let 't' a possible arrival time and 'w' the
    value of '--show-len' parameter, the application will plot data in
    the interval [t - w, t + w] for that event.
    Default value is 30.0 seconds.
        ''')

        # Parse the args and call whatever function was selected
        args, _ = parser.parse_known_args()
        print_settings(args)

    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2

    args.func(**vars(args))

if __name__ == "__main__":
    sys.exit(main())
