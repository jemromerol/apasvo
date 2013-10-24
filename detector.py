#!/usr/bin/python2.7
# encoding: utf-8
'''
detector

detector is a description

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

import matplotlib.pyplot as pl
import argparse
import os
import sys

from _version import __version__
from utils import clt, parse, collections
from picking import stalta, ampa
from picking import record as rc


def draw_events_table(record, method):
    """"""
    sys.stdout.write("%i possible events found in %s:\n" %
                     (len(record.events), record.filename))
    sys.stdout.flush()
    et = [e.time for e in record.events]
    cf_val = [e.cf_value for e in record.events]
    if len(et) > 0:
        sys.stdout.write("\n%s\n\n" %
                         clt.Table(clt.Column("No.", range(1, len(et) + 1)),
                                     clt.Column("Time(s)", et),
                                     clt.Column("%s CF Value" % method.upper(),
                                                cf_val)))
        sys.stdout.flush()


def draw_results(records, method):
    """"""
    # Extract data from records
    data = [{'file_name':record.filename,
             'time':event.time,
             'cf_value': event.cf_value} for record in records
                                            for event in record.events]
    sys.stdout.write("Summary of events:\n")
    sys.stdout.write("\n%s\n\n" %
                     clt.Table(clt.Column("File Name",
                                          [e['file_name'] for e in data],
                                          fmt='%s'),
                                 clt.Column("Time(s)",
                                            [e['time'] for e in data]),
                                 clt.Column("%s CF Value" % method.upper(),
                                            [e['cf_value'] for e in data])))
    sys.stdout.flush()


def print_settings(args):
    """"""
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
                                       args.window_overlap))
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
    """
    """

    def run(self, FILEIN, csv=False, cf=False, **kwargs):
        """"""
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
        pl.ion()
        self._do_analysis(records, alg, **kwargs)
        pl.ioff()
        pl.close('all')

        #Set the method used in events
        methods = {('stalta', False): 1, ('stalta', True): 2,
                   ('ampa', False): 3, ('ampa', True): 4}
        for record in records:
            for event in record.events:
                event.method = rc.Event.methods[methods.get((method, takanami),
                                                            0)]
        # Show results
        draw_results(records, method=method)

        # Generate reports
        if csv is True:
            self.on_notify("Generating CSV report in %s... " % csv.name)
            rc.generate_csv(records, csv)
            self.on_notify("Done\n")

        # Save cf
        if cf:
            for record in records:
                fname = "%s.cf" % record.filename
                self.on_notify("Saving CF for input file %s in %s... " %
                               (record.filename, fname))
                record.save_cf(fname, fmt=kwargs.get('cff', 'binary'),
                               dtype=kwargs.get('cfd', 'float64'),
                               byteorder=kwargs.get('cfb', 'native'))
                self.on_notify("Done\n")

    def _do_analysis(self, records, supervised=False, **kwargs):
        """"""
        raise NotImplementedError

    def _supervise_events(self, record, takanami=True, show_len=5.0,
                          show_cf=False, show_specgram=False,
                          show_envelope=False,
                          show_all=False, **kwargs):
        """"""
        raise NotImplementedError

    def on_notify(self, msg):
        """"""
        pass


class Detector(Analysis):
    """
    """

    def _do_analysis(self, records, alg, supervised=False, **kwargs):
        """"""
        # Extract method name from kwargs
        method = kwargs.get('method', 'ampa')
        for record in records:
            self.on_notify("Processing %s... " % record.filename)
            record.detect(alg, **kwargs)
            self.on_notify("Done\n")
            draw_events_table(record, method)
            if supervised:
                last_response = self._supervise_events(record, **kwargs)
                if last_response == "quit":
                    break
                elif last_response == "continue & don't ask again":
                    supervised = False
                    pl.close('all')

    def _supervise_events(self, record, takanami=True, show_len=5.0,
                          show_cf=False, show_specgram=False,
                          show_envelope=False,
                          show_all=False, **kwargs):
        """"""
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
            record.plot_signal(t_start=event.time - show_len,
                               t_end=event.time + show_len,
                               num=1,
                               show_cf=show_cf,
                               show_specgram=show_specgram,
                               show_envelope=show_envelope,
                               **kwargs)
            if takanami:
                record.plot_aic(event, num=2, show_envelope=show_envelope)
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
    """
    """

    def _do_analysis(self, records, alg, supervised=False, **kwargs):
        """"""
        # Extract method name from kwargs
        method = kwargs.get('method', 'ampa')
        for record in records:
            self.on_notify("Processing %s... " % record.filename)
            if supervised:
                record.detect(alg, threshold=0.0, **kwargs)
                self.on_notify("Done\n")
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

    def _supervise_events(self, record, takanami=True, show_len=5.0,
                          show_cf=False, show_specgram=False,
                          show_envelope=False,
                          show_all=False, **kwargs):
        """"""
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
                record.plot_aic(event, num=2, show_envelope=show_envelope)
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
    """"""
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

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_version_message = '%%(prog)s %s' % program_version
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Jose Emilio Romero Lopez.
  Copyright 2013. All rights reserved.

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

USAGE
''' % program_shortdesc

    try:
        # Setup argument parser
        parser = parse.CustomArgumentParser(description=program_license,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                fromfile_prefix_chars='@')

        #Create common arguments for all commands
        parser = argparse.ArgumentParser()
        parser.set_defaults(func=analysis)
        parser.add_argument('-V', '--version', action='version',
                            version=program_version_message)
        parser.add_argument("--datatype",
                            choices=['float16', 'float32', 'float64'],
                            default='float64',
                            help='''
        If the input files are in binary format this will be
        the datatype used for reading it.
                            ''')
        parser.add_argument("--byteorder",
                                   choices=['little-endian', 'big-endian',
                                            'native'],
                                   default='native',
                                   help='''
        If the input files are in binary format this will be the byte-order
        of the selected datatype. Default choice is hardware native.
                                   ''')

        parser.add_argument("FILEIN", nargs='+',
                                     action=parse.GlobInputFilenames,
                                     help='''
        Binary or text file containing a seismic-like signal.
        ''')
        parser.add_argument("--csv", type=argparse.FileType('w'),
                                     default="output.csv",
                                     help='''
        Generates an report in csv format. If none is specified will generate
        a csv file named output.csv containing the list of events found.
        ''')
        # Arguments to store the characteristic function
        parser.add_argument("--cf", action="store_true", default=False,
                            help='''
                            If selected a file containing the corresponding characteristic function
                            will be generated for each of the input files. The name of the new file
                            will be the same of the input file followed by '.cf'.''')
        parser.add_argument("--cff", choices=["binary", "text"],
                            default="binary",
                            help='''
                            Output format for the characteristic function.
                            Default value is 'binary'.''')
        parser.add_argument("--cfd", choices=['float16', 'float32', 'float64'],
                            default='float64',
                            help='''
        If the characteristic function is saved in binary format, this will be the selected datatype.
        Default choice is hardware native.''')
        parser.add_argument("--cfb", choices=['little-endian', 'big-endian', 'native'],
                            default='native',
                            help='''
        If the characteristic function is saved in binary format, this will be the byte-order
        of the selected datatype. Default choice is hardware native.''')
        parser.add_argument("-f", "--frequency", type=parse.positive_float,
                                     default=50.0,
                                     dest='fs',
                                     help="Signal frequency.")
        parser.add_argument("-m", "--method",
                                   choices=['ampa', 'stalta'],
                                   help='''
                                   Available methods. Default method is AMPA.
                                   ''', default='ampa')
        parser.add_argument("--peak-checking",
                                   type=parse.positive_float,
                                   default=5.0,
                                   help='''
        How many seconds need to be examined before and after
        a sample to consider it a local maximum.
        Default value is 5 seconds.
        ''')
        # STA-LTA arguments
        sta_lta_options = parser.add_argument_group("STA-LTA options")
        sta_lta_options.add_argument("--sta-window",
                                     type=parse.positive_float,
                                     dest='sta_length',
                                     default=5.0,
                                     help='''
        Length of STA window (in seconds) when using the STA-LTA method.
        Default value is 5 seconds.
        ''')
        sta_lta_options.add_argument("--lta-window",
                                     type=parse.positive_float,
                                     dest='lta_length',
                                     default=600.0,
                                     help='''
        Length of LTA window (in seconds) when using the STA-LTA method.
        Default value is 600 seconds.
        ''')
        # AMPA arguments
        ampa_options = parser.add_argument_group("AMPA options")
        ampa_options.add_argument("--ampa-window",
                                  type=parse.positive_float,
                                  dest='window',
                                  default=150.0,
                                  help='''
        Length of the window (in seconds) when using the AMPA method.
        Usually this value should be close to the expected length
        of the events we are looking for. Default value is 100 seconds.
        ''')
        ampa_options.add_argument("--ampa-window-overlap",
                                  type=parse.fraction,
                                  dest='window_overlap',
                                  default=0.5,
                                  help='''
        Overlapping value between windows when using the AMPA method.
        Must be in range [0,1). Default value is 0.5.
        ''')
        ampa_options.add_argument("--ampa-L",
                                  type=parse.positive_float,
                                  dest='L',
                                  default=[30.0, 20.0, 10.0, 5.0, 2.5],
                                  nargs='+',
                                  help='''
        Set of filter lengths (in seconds) used by AMPA
        in the enhancement stage. Default values are 30.0, 20.0,
        10.0, 5.0 and 2.5 seconds.
        ''')
        ampa_options.add_argument("--ampa-L-coef",
                                  type=float,
                                  dest='L_coef',
                                  default=3.0,
                                  help='''
        Penalty factor which minimizes response to emerging or impulsive noise
        on the set of filters applied in the enhancement stage.
        Default value is 3.0.
        ''')
        ampa_options.add_argument("--ampa-noise-threshold",
                                  type=parse.percentile,
                                  dest='noise_thr',
                                  default=90.0,
                                  help='''
        Percentile used in the noise reduction stage. Default value is 90.0.
        ''')
        ampa_options.add_argument("--ampa-f-start",
                                  type=parse.positive_float,
                                  dest='f_start',
                                  default=2.0,
                                  help='''
        Start frequency of the filter bank applied in the adaptive multi-band
        processing stage. Default value is 2Hz.
        ''')
        ampa_options.add_argument("--ampa-f-end",
                                  type=parse.positive_float,
                                  dest='f_end',
                                  default=12.0,
                                  help='''
        End frequency of the filter bank applied in the adaptive multi-band
        processing stage. Default value is 12Hz.
        ''')
        ampa_options.add_argument("--ampa-bandwidth",
                                  type=parse.positive_float,
                                  dest='bandwidth',
                                  default=3.0,
                                  help='''
        Channel bandwidth of the filter bank applied in the adaptive multi-band
        processing stage. Default value is 3Hz.
        ''')
        ampa_options.add_argument("--ampa-overlap",
                                  type=parse.positive_float,
                                  dest='overlap',
                                  default=1.0,
                                  help='''
        Overlap between channels of the filter bank applied in the adaptive
        multi-band processing stage. Default value is 1Hz.
        ''')
        ampa_options.add_argument("--ampa-U",
                                  type=float,
                                  dest='U',
                                  default=12.0,
                                  help='''
        Term used to avoid the logarithm of zero in the calculation of the
        characteristic function. Default value is 12.0.
        ''')
        # Takanami arguments
        takanami_options = parser.add_argument_group("Takanami options")
        takanami_options.add_argument("--takanami",
                                 action='store_true',
                                 default=False,
                                 help='''
        Use the Takanami AR method to refine results.
        ''')

        takanami_options.add_argument("--takanami-margin",
                                 type=parse.positive_float,
                                 default=5.0,
                                 help='''
        When using the Takanami method how many seconds
        will be examined before and after a picked event.
        ''')

        # Create arguments for the supervised mode
        supervised_options = parser.add_argument_group("Supervised mode")
        supervised_options.add_argument("-s", "--supervised",
                                        action="store_true", default=False,
                                        help='''
        Enables supervised mode.
        ''')
        supervised_options.add_argument("--show-all",
                                        action='store_true', default=False,
                                        help='''
        Equivalent to --show-cf --show_envelope --show-specgram
        ''')
        supervised_options.add_argument("--show-cf",
                                        action="store_true", default=False,
                                        help='''
        Shows the characteristic function in supervised mode.
        ''')
        supervised_options.add_argument("--show-specgram",
                                        action="store_true", default=False,
                                        help='''
        Shows the spectrogram in supervised mode.
        ''')
        supervised_options.add_argument("--show-envelope",
                                        action="store_true", default=False,
                                        help='''
        Display signal envelope in supervised mode.
        ''')
        supervised_options.add_argument("--show-len",
                                        type=parse.positive_float,
                                        default=5.0,
                                        help='''
        How many seconds of the input signal will be displayed before and after
        of a possible event.
        Default value is 5.0 seconds.
        ''')
        # Create arguments for "detect" command
        parser.add_argument("--sort", choices=['td', 'ta', 'vd', 'va'],
                                   help='''
        How the results are sorted. Choices are
        time descending/ascending and characteristic
        function value descending/ascending. Default
        value is time ascending.
                                   ''', default='ta')
        parser.add_argument("-t", "--threshold", type=parse.positive_float,
                                   help='''
        Characteristic Function value from which a local maximum
        can be considered a P-phase arrival event. Default value is 2.0.
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
