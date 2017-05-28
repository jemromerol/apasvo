#!/usr/bin/python2.7
# encoding: utf-8
'''Earthquake Generator
A tool that generates synthetic seismic signals.

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
import os
import sys

from apasvo._version import __version__
from apasvo.utils import clt, parse, futils
from apasvo.utils.formats import rawfile
from apasvo.picking import eqgenerator


def print_settings(args):
    """Prints settings to stdout.

    Args:
        args: Command-line input arguments.
    """
    sys.stdout.write("\nGeneral settings:\n")
    sys.stdout.write("%30s: %s\n" % ("Signal frequency(Hz)",
                                     args.fs))
    sys.stdout.write("%30s: %s\n" % ("Length(s)",
                                     args.length))
    sys.stdout.write("%30s: %s\n" % ("Start time(s)",
                                     args.t_event))
    sys.stdout.write("%30s: %s\n" % ("Noise power(dB)",
                                     args.P_noise_db))
    if not args.FILEIN:
        sys.stdout.write("%30s: %s\n" % ("Event power(dB)",
                                         args.gen_event_power))
        sys.stdout.write("\nFilter bank settings:\n")
        sys.stdout.write("%30s: %s\n" % ("Start frequency(Hz)",
                                       args.f_low))
        sys.stdout.write("%30s: %s\n" % ("End frequency(Hz)",
                                       args.f_high))
        sys.stdout.write("%30s: %s\n" % ("Subband bandwidth(Hz)",
                                       args.bandwidth))
        sys.stdout.write("%30s: %s\n" % ("Subband overlap(Hz)",
                                       args.overlap))
        sys.stdout.write("%30s: %s\n" % ("Start envelope length(s)",
                                       args.low_period))
        sys.stdout.write("%30s: %s\n" % ("End envelope length(s)",
                                       args.high_period))
        sys.stdout.write("%30s: %s\n" % ("Start amplitude",
                                       args.low_amp))
        sys.stdout.write("%30s: %s\n" % ("End amplitude",
                                       args.high_amp))

    sys.stdout.write("\n")
    sys.stdout.flush()


def generate(FILEIN, length, t_event, output, gen_event_power=5.0, n_events=1,
             gen_noise_coefficients=False, output_format='binary',
             datatype='float64', byteorder='native', **kwargs):
    """Generates synthetic earthquake signals with background noise and saves
    them to file.

    The function accepts a list of command-line arguments and renders synthetic
    seismic data in two ways: If a list of input files containing seismic data
    is provided, the function generates a new output signal for each one of
    the files by adding background noise. If no input file is provided,
    the function generates a list of synthetic seismic signals.

    Args:
        FILEIN: A list of binary or text file objects storing seismic data.
        length: Length of rendered seismic signals, in seconds.
            If FILEIN is None, this parameter has no effect.
        t_event: Start time of rendered earthquake, given in seconds from the
            beginning of the signal.
            If FILEIN is None, this parameter has no effect.
        output: Output file name (absolute path).
            If no input file is provided and n_events is greater than 1, the
            name of each generated file will be followed by its ordinal number.

            E.g. given FILEIN = None, output = 'example.out' and n_events = 5,
            the function will generate 5 synthetic files named:
            'example00.out', 'example01.out', 'example02.out', 'example03.out'
            and 'example04.out'.

        gen_event_power: Earthquake power in dB.
            If FILEIN is None, this parameter has no effect.
            Default: 5.0.
        n_events: No. of signals to generate.
            If FILEIN is None, this parameter has no effect.
            Default: 1.
        gen_noise_coefficients: A binary or text file object containing a list
            of numeric coefficients of a FIR filter that models the background
            noise.
            Default value is False, meaning unfiltered white noise is used
            to model the background noise.
        output_format: Output file format. Possible values are 'binary' or
            'text'. Default: 'binary'.
        datatype: Data-type of generated data. Default value is 'float64'.
            If FILEIN is not None, this parameter is also the datatype of
            input data.
        byteorder: Byte-order of generated data. Possible values are
            'little-endian', 'big-endian' and 'native'.
            If FILEIN is not None, this parameter is also the format of
            input data.
            Default value is 'native'.
    """
    fs = kwargs.get('fs', 50.0)
    # Configure generator
    clt.print_msg("Configuring generator... ")
    generator = eqgenerator.EarthquakeGenerator(**kwargs)
    clt.print_msg("Done\n")
    # Load noise coefficients
    if gen_noise_coefficients:
        if futils.istextfile(gen_noise_coefficients):
            f = open(gen_noise_coefficients, 'r')
        else:
            f = open(gen_noise_coefficients, 'rb')
        clt.print_msg("Loading noise coefficients from %s... " %
                         f.name)
        generator.load_noise_coefficients(f, dtype=datatype,
                                          byteorder=byteorder)
        clt.print_msg("Done\n")
    # Process input files
    basename, ext = os.path.splitext(output)
    filename_out = output
    # If a list of input files containing seismic data
    # is provided, generate a new output signal for each one of
    # the files by adding background noise.
    if FILEIN:
        fileno = 0
        for f in FILEIN:
            # Read input signal
            fin_handler = rawfile.get_file_handler(f, dtype=datatype,
                                                   byteorder=byteorder)
            clt.print_msg("Loading seismic signal from %s... " %
                          fin_handler.filename)
            signal = fin_handler.read()
            clt.print_msg("Done\n")
            # Generate output filename
            if len(FILEIN) > 1:
                filename_out = "%s%02.0i%s" % (basename, fileno, ext)
                fileno += 1
            clt.print_msg("Generating artificial signal in %s... " %
                             filename_out)
            # Add background noise to signal
            eq = generator.generate_noise(signal)
            # Save outputs to file
            if output_format == 'text':
                fout_handler = rawfile.TextFile(filename_out, dtype=datatype,
                                            byteorder=byteorder)
            else:
                fout_handler = rawfile.BinFile(filename_out, dtype=datatype,
                                              byteorder=byteorder)
            fout_handler.write(eq, header="Sample rate: %g Hz." % fs)
            clt.print_msg("Done\n")
    # If no input file is provided,
    # generate a list of synthetic seismic signals.
    else:
        for i in xrange(n_events):
            # Generate output filename
            if n_events > 1:
                filename_out = "%s%02.0i%s" % (basename, i, ext)
            clt.print_msg("Generating artificial signal in %s... " %
                             filename_out)
            # Generate a synthetic signal
            eq = generator.generate_earthquake(length, t_event,
                                               gen_event_power)
            # Save outputs to file
            if output_format == 'text':
                fout_handler = rawfile.TextFile(filename_out, dtype=datatype,
                                                byteorder=byteorder)
            else:
                fout_handler = rawfile.BinFile(filename_out, dtype=datatype,
                                byteorder=byteorder)
            fout_handler.write(eq, header="Sample rate: %g Hz." % fs)
            clt.print_msg("Done\n")


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

    A tool that generates synthetic seismic signals.

    Renders synthetic seismic data in two ways: If a list of input files
    containing seismic data is provided, the tool generates a new output
    signal for each one of them by adding background noise. If no input
    file is provided, it generates a list of synthetic seismic signals.

    Artificial earthquakes are generated at desired start point from
    white noise band-filtered and modulated by using different envelope
    functions for each band.
    Similarly, background noise is modeled from white noise and finally
    added to the previously generated sequence that contains the synthetic
    earthquake.


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

    \033[1m>> python apasvo-generator.py -o example.out -f 100 -l 600 -t 200 -ep 5 -np 0\033[0m

    Generates a synthetic earthquake of the following characteristics:

        Earthquake power: 5.0 dB (SNR 5.0)
        Noise power: 0.0 dB (SNR 5.0)
        Sample rate: 100 Hz.
        Length: 600.0 seconds (10 minutes)
        Arrival time: 200.0 seconds.

    Saves result to a file named 'example.out'


    \033[1m>> python apasvo-generator.py meq.bin meq2.txt -f 50 -np 2 -fir coeffs.txt\033[0m

    Given two seismic signals, 'meq.bin' and 'meq2.txt', sample rate 50 Hz, adds
    background noise of 2.0 dB. Noise is modeled by a FIR filter whose
    coefficients are stored in the file 'coeffs.txt'.

    Results will be saved to 'eq00.out' and 'eq01.out'.


    \033[1m>> python apasvo-generator.py -o eq.bin -n 500 -l 3600 -t 100 -ep 2 -np 2 --f-low 4.0 --f-high 25.0\033[0m

    Generates a list of 500 synthetic earthquakes of the following
    characteristics:

        SNR: 0.0 (2.0 dB signal and noise power)
        Sample rate: 50 Hz. (Default value).
        Frequency range: 4-25 Hz.
        Background noise: Gaussian white noise.
        Length: 3600 seconds.
        Arrival time: 100.0 seconds.

    Results will be saved to 'eq00.bin', 'eq01.bin', 'eq02.bin', ...,
    'eq499.bin'.


    \033[1m>> python apasvo-generator.py -o eq.txt -n 30 --output-format text @settings.txt\033[0m

    Generates a list of 30 synthetic earthquakes and takes some settings from a
    text file named 'settings.txt'
    Saves them to 'eq00.txt', ..., 'eq29.txt', plain text format.

    Rendered signals has the following characteristics:

        Earthquake power: 10.0 dB.
        Noise power: 0.0 dB.
        FIR filter coefficients: 'coeffs.txt'
        Length: 1200 seconds.
        Arrival time: 250.0 seconds.

    So, the following is the content of 'settings.txt':

    >> cat settings.txt
    -ep 10.0
    -np 0.0
    -fir coeffs.txt
    -l 1200
    -t 250
    '''
    try:
        # Setup argument parser
        parser = parse.CustomArgumentParser(description=program_description,
                                            epilog=program_examples,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                fromfile_prefix_chars='@')
        parser.add_argument('-V', '--version', action='version',
                            version=program_version_message)
        parser.set_defaults(func=generate)
        parser.add_argument("FILEIN", nargs='*',
                            action=parse.GlobInputFilenames,
                            metavar='file',
                            help='''
    Binary or text file containing a seismic-like signal.
        ''')
        parser.add_argument("-o", "--output",
                            default='eq.out',
                            metavar='<file>',
                            help='''
    Output filename. Default: 'eq.out'.
    If no. of output signals is greater than 1, basename of each
    generated file will be followed by its ordinal number.
    E.g. given parameters '-o example.out' and '-n 5', generates 5 files named:
    'example00.out', 'example01.out', 'example02.out', 'example03.out'
    and 'example04.out'.
        ''')
        parser.add_argument("-n", "--n-events",
                            type=parse.positive_int,
                            default=1,
                            metavar='<arg>',
                            help='''
    No. of signals to generate. Default: 1.
    If input signal is provided, this parameter has no effect.
        ''')
        parser.add_argument("-f", "--frequency", type=parse.positive_int,
                            default=50,
                            dest='fs',
                            metavar='<arg>',
                            help='''
    Sample rate in Hz. Default: 50 Hz.
        ''')
        parser.add_argument("-l", "--length",
                            type=parse.positive_int,
                            default=600.0,
                            metavar='<arg>',
                            help='''
    Length of generated data in seconds.
    If input file is provided, this parameter has no effect.
    Default: 600.0 seconds.
        ''')
        parser.add_argument("-t", "--t-event",
                            type=parse.positive_float,
                            default=50.0,
                            metavar='<arg>',
                            help='''
    Arrival time in seconds from the beginning of rendered signal.
    If input signal is provided, this parameter has no effect.
    Default: 50.0 seconds.
        ''')
        parser.add_argument("-ep", "--earthquake-power",
                            type=float,
                            dest='gen_event_power',
                            default=10.0,
                            metavar='<arg>',
                            help='''
    Earthquake power in dB.
    If input signal is provided, this parameter has no effect.
    Default: 10.0 dB.
        ''')
        parser.add_argument("-np", "--noise-power",
                            type=float,
                            dest='P_noise_db',
                            default=0.0,
                            metavar='<arg>',
                            help='''
    Background noise power in dB. Default: 0.0 dB.
        ''')
        parser.add_argument("-fir", "--noise-coefficients",
                            type=parse.filein,
                            dest='gen_noise_coefficients',
                            metavar='<file>',
                            help='''
    Binary or text file containing a list of numeric coefficients of a
    FIR filter that characterizes background noise. If not specified
    unfiltered white noise is used to model background noise.
        ''')
        parser.add_argument("--f-low",
                            type=parse.positive_float,
                            dest='f_low',
                            default=2.0,
                            metavar='<arg>',
                            help='''
    Start frequency on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 2.0 Hz.
        ''')
        parser.add_argument("--f-high",
                            type=parse.positive_float,
                            dest='f_high',
                            default=18.0,
                            metavar='<arg>',
                            help='''
    End frequency on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 18.0 Hz.
        ''')
        parser.add_argument("--bandwidth",
                            type=parse.positive_float,
                            dest='bandwidth',
                            default=4.0,
                            metavar='<arg>',
                            help='''
    Channel bandwidth on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 4.0 Hz.
        ''')
        parser.add_argument("--overlap",
                            type=parse.positive_float,
                            dest='overlap',
                            default=1.0,
                            metavar='<arg>',
                            help='''
    Overlap between channels bank on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 1.0 Hz.
        ''')
        parser.add_argument("--period-low",
                            type=parse.positive_float,
                            dest='low_period',
                            default=50.0,
                            metavar='<arg>',
                            help='''
    Start value of the range of noise envelope lengths for the
    different bands on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 50.0 seconds.
        ''')
        parser.add_argument("--period-high",
                            type=parse.positive_float,
                            dest='high_period',
                            default=10.0,
                            metavar='<arg>',
                            help='''
    End value of the range of noise envelope lengths for the
    different bands on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 10.0 seconds.
        ''')
        parser.add_argument("--amplitude-low",
                            type=parse.positive_float,
                            dest='low_amp',
                            default=0.2,
                            metavar='<arg>',
                            help='''
    Start value of the range of noise envelope amplitudes for the
    different bands on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 0.2.
        ''')
        parser.add_argument("--amplitude-high",
                            type=parse.positive_float,
                            dest='high_amp',
                            default=0.1,
                            metavar='<arg>',
                            help='''
    End value of the range of noise envelope amplitudes for the
    different bands on multi-band earthquake synthesis.
    If input signal is provided, this parameter has no effect.
    Default: 0.1.
        ''')
        parser.add_argument("--output-format",
                            choices=["binary", "text"],
                            default="binary",
                            help='''
    Output file format. Default value is 'binary'.
        ''')
        parser.add_argument("--datatype",
                            choices=['int16', 'int32', 'int64', 'float16', 'float32', 'float64'],
                            default='float64',
                            help='''
    Data-type of generated data. If input files are specified, this parameter
    is also the data-type of data stored on them.
    Default value is float64, meaning double-precision floating point format.
        ''')
        parser.add_argument("--byteorder",
                            choices=['little-endian', 'big-endian', 'native'],
                            default='native',
                            help='''
    Byte-ordering for generated data. If input files are specified, this
    parameter is also the byte-ordering for data stored on them.
    Default value is 'native', meaning platform native byte-ordering.
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
