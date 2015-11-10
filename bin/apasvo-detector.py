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
import itertools
import multiprocessing

from apasvo._version import __version__
from apasvo.utils import parse
from apasvo.utils import collections
from apasvo.picking import stalta
from apasvo.picking import ampa
from apasvo.picking import apasvotrace as rc


INPUT_FORMAT_MAP = {
    'binary': 'binary',
    'text': 'text',
    'autodetect': None,
    'sac': 'SAC',
    'mseed': 'MSEED',
}

OUTPUT_FORMAT_MAP = {
    'nonlinloc': 'NLLOC_OBS',
    'quakeml': 'QUAKEML',
    'json': 'JSON',
}

OUTPUT_EXTENSION_SET = {
    'NLLOC_OBS': '.hyp',
    'QUAKEML': '.xml',
    'JSON': '.json',
}

METHOD_MAP = {
    'stalta': stalta.StaLta,
    'ampa': ampa.Ampa,
}

DEFAULT_INPUT_FORMAT = 'autodetect'
DEFAULT_OUTPUT_FORMAT = 'nonlinloc'
DEFAULT_METHOD = 'ampa'


def print_settings(**kwargs):
    """Print settings to stdout.

    Args:
        args: Command-line input arguments.
    """
    sys.stdout.write("\n*** General settings ***\n")
    # Print multiprocessing settings
    allow_multiprocessing = not kwargs.get('no_multiprocessing')
    sys.stdout.write("%30s: %s\n" % ("Allow multiprocessing", allow_multiprocessing))
    if allow_multiprocessing:
        sys.stdout.write("%30s: %s\n" % ("N. of processes", kwargs.get('processes')))
    if kwargs.get('threshold'):
        sys.stdout.write("%30s: %s\n" % ("Threshold", kwargs.get('threshold')))
    if kwargs.get('threshold'):
        sys.stdout.write("%30s: %s\n" % ("Threshold", kwargs.get('threshold')))
    sys.stdout.write("%30s: %s\n" % ("Output format", kwargs.get('output_format', '').upper()))
    sys.stdout.write("%30s: %s\n" % ("Peak checking(s)", kwargs.get('peak_checking')))
    sys.stdout.write("%30s: %s\n" % ("Algorithm used", kwargs.get('method', '').upper()))
    sys.stdout.write("%30s: %s\n" % ("Takanami", kwargs.get('takanami')))
    sys.stdout.write("%30s: %s\n" % ("Takanami margin", kwargs.get('takanami_margin')))
    if kwargs.get('method') == 'ampa':
        sys.stdout.write("\n*** AMPA settings ***\n")
        sys.stdout.write("%30s: %s\n" % ("Window length(s)", kwargs.get('window')))
        sys.stdout.write("%30s: %s\n" % ("Window overlap", kwargs.get('step')))
        sys.stdout.write("%30s: %s\n" % ("Noise threshold", kwargs.get('noise_thr')))
        sys.stdout.write("%30s: %s\n" % ("Length of the filters used(s)", kwargs.get('L')))
        sys.stdout.write("%30s: %s\n" % ("Negative response coefficient", kwargs.get('L_coef')))
        sys.stdout.write("%30s: %s\n" % ("Coefficient U", kwargs.get('U')))
        sys.stdout.write("\n*** AMPA filter bank settings ***\n")
        sys.stdout.write("%30s: %s\n" % ("Start frequency(Hz)", kwargs.get('f_start')))
        sys.stdout.write("%30s: %s\n" % ("End frequency(Hz)", kwargs.get('f_end')))
        sys.stdout.write("%30s: %s\n" % ("Subband bandwidth(Hz)", kwargs.get('bandwidth')))
        sys.stdout.write("%30s: %s\n" % ("Subband overlap(Hz)", kwargs.get('overlap')))
    if kwargs.get('method') == 'stalta':
        sys.stdout.write("\n*** STA-LTA settings ***\n")
        sys.stdout.write("%30s: %s\n" % ("STA window length(s)", kwargs.get('sta_length')))
        sys.stdout.write("%30s: %s\n" % ("LTA window length(s)", kwargs.get('lta_length')))
    sys.stdout.write("\n")
    sys.stdout.flush()


def analysis_single_file_task(filename, **kwargs):
    """

    :param file:
    :param kwargs:
    """
    # Get debug level
    debug = kwargs.get('verbosity', 1)
    # Configure algorithm
    method = METHOD_MAP.get(kwargs.get('method', DEFAULT_METHOD), ampa.Ampa)
    alg = method(**kwargs)
    # Open input file
    if debug:
        print "*** Processing file {} ***".format(filename)
    input_format = INPUT_FORMAT_MAP.get(kwargs.get('input_format', DEFAULT_INPUT_FORMAT))
    stream = rc.read(filename, format=input_format, **kwargs)
    if debug:
        print "Traces in {}".format(filename)
        print stream
    # Pick stream traces
    for trace in stream.traces:
        trace.detect(alg, debug=debug, **kwargs)
    # Export picks
    ouput_format = OUTPUT_FORMAT_MAP.get(kwargs.get('output_format', DEFAULT_OUTPUT_FORMAT))
    extension = OUTPUT_EXTENSION_SET.get(ouput_format, '')
    basename, _ = os.path.splitext(os.path.basename(filename))
    output_path = kwargs.get('destination_path', os.getcwd())
    stream_suffix = '_'.join([suffix for tr in stream.traces
                             for suffix in tr.getId().split('.')
                             if suffix != ''])
    output_filename = "{}_{}{}".format(basename, stream_suffix, extension)
    stream.export_picks(os.path.join(output_path, output_filename), format=ouput_format, debug=debug)


def analysis_chunk_task(parameters):
    """
    :param parameters:
    """
    file_list = parameters[0]
    kwargs = parameters[1]
    for file in file_list:
        analysis_single_file_task(file, **kwargs)


def analysis(**kwargs):
    """Performs event analysis/picking over a set of seismic signals.

    Performs event detection if parameter 'threshold' is not None, otherwise
    performs event picking.
    """
    # Get file list
    file_list = kwargs.pop('FILEIN', [])

    # Get debug level
    debug = kwargs.get('verbosity', 1)

    if debug:
        print_settings(**kwargs)

    if kwargs.get('no_multiprocessing', False):
        analysis_chunk_task((file_list, kwargs))
    else:
        processes = kwargs.get('processes', multiprocessing.cpu_count())
        p = multiprocessing.Pool(processes=processes)
        p.map(analysis_chunk_task, itertools.izip(collections.chunkify(file_list, len(file_list) / processes),
                                            itertools.repeat(kwargs)))
        p.close()
        p.join()


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

    \033[1m>> python apasvo-detector.py meq01.txt -o nonlinloc -m stalta --lta 60 --takanami\033[0m

    Let 'meq01.txt' a text file containing seismic data, performs event picking
    with the following settings:

        Sample rate: 50 Hz. (Default value).
        Picking Algorithm: STA-LTA.
            STA window length: 5.0 seconds. (Default value).
            LTA window length: 60.0 seconds.
        Apply Takanami AR method on results.

    Works on supervised mode, showing characteristic function, envelope
    function and espectrogram for each possible event.
    Saves results to nonlinloc format

    \033[1m>> python apasvo-detector.py meq01.bin -t 1.5 --ampa-filters 50.0 25.0 12.5 6.25  --ampa-noise-threshold 75\033[0m

    Let 'meq01.bin' a binary file containing seismic data, detects seismic
    events whose characteristic function value is over 1.5.
    Event detection uses the following settings:

        Detection Algorithm: AMPA.
            Filter lengths: 50.0 25.0 12.5 6.25 (in seconds).
            Noise threshold percentile: 75

    Saves results summary to nonlinloc format.
    Saves characteristic function to './cf_data/meq01.cf.bin'.

    \033[1m>> python apasvo-detector.py meq*.bin --output-format quakeml @settings.txt\033[0m

    Performs event picking on all files matching 'meq*.bin' and takes some
    settings from a text file named 'settings.txt'.
    Saves results to quakeml format.

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
        parser.add_argument('-V', '--version', action='version',
                            version=program_version_message)
        parser.add_argument('-v', '--verbosity',
                            type=parse.non_negative_int,
                            default=1,
                            metavar='<arg>',
                            help='''
    Verbosity level. A value of 0 means no output is printed. Default value is 1.
        ''')
        parser.add_argument("FILEIN", nargs='+',
                            action=parse.GlobInputFilenames,
                            metavar='file',
                            help='''
    Binary or text file containing a seismic-like signal.
        ''')
        parser.add_argument("-i", "--input-format",
                            choices=['binary', 'text', 'sac', 'mseed', 'autodetect'],
                            default='autodetect',
                            help='''
    Selected format for input files. Default value is autodetect, meaning
    format will be inferred for each input file.
        ''')
        parser.add_argument("-o", "--output-format",
                            choices=['nonlinloc', 'quakeml', 'json'],
                            default='nonlinloc',
                            help='''
    Output file format for the picked events. Default: 'nonlinloc'.
        ''')
        parser.add_argument("-d", "--destination-path",
                            metavar='<arg>',
                            default=os.getcwd(),
                            help='''
    Destination path for output files. By default it will be the current working directory.
        ''')
        parser.add_argument("--no-multiprocessing",
                            action='store_true',
                            default=False,
                            help='''
    Do not use multiprocessing during pick estimation.
        ''')
        parser.add_argument("-p", "--processes",
                            type=parse.positive_int,
                            default=multiprocessing.cpu_count(),
                            metavar='<arg>',
                            help='''
    Number of processes to be used during pick estimation. By default it will be equal to
    the number of system processors.
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
        parser.add_argument("-f", "--frequency", type=parse.positive_int,
                            default=50.0,
                            dest='fs',
                            metavar='<arg>',
                            help='''
    Sample rate in Hz (only has effect for binary and text input files). Default: 50 Hz
        ''')
        parser.add_argument("--datatype",
                            choices=['int16', 'int32', 'int64', 'float16', 'float32', 'float64'],
                            default='float64',
                            dest='dtype',
                            help='''
    Data-type of input data (only has effect for binary input files).
    Default value is float64, meaning double-precision floating point format.
        ''')
        parser.add_argument("--byteorder",
                            choices=['little-endian', 'big-endian', 'native'],
                            default='native',
                            help='''
    If the input files are in binary format this will be the byte-order
    of the selected datatype. Default choice is hardware native.
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

        # Parse the args and call whatever function was selected
        args, _ = parser.parse_known_args()

    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2

    analysis(**vars(args))

if __name__ == "__main__":
    sys.exit(main())
