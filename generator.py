#!/usr/bin/python2.7
# encoding: utf-8
'''Earthquake Generator
A tool to generate synthetic seismic signals.

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

import argparse
import os
import sys

from _version import __version__
from utils import clt, parse, futils
from utils.formats import rawfile
from picking import eqgenerator


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
    sys.stdout.write("%30s: %s\n" % ("Noise power(dB))",
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
            If FILEIN is not None, this parameter is also the format of
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
                rawfile.BinFile(filename_out, dtype=datatype,
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
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_description = '''
    %s %s

    %s

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

    ''' % (program_name, program_version, program_shortdesc)
    program_examples = '''
    Examples of use:

    \033[1m>> detector.py -o example.out -f 100 -l 600 -t 200 -ep 5 -np 0\033[0m

    Generates a synthetic earthquake of the following characteristics:

        Earthquake power: 5.0 dB (SNR 5.0)
        Noise power: 0.0 dB (SNR 5.0)
        Sample rate: 100 Hz.
        Length: 600.0 seconds (10 minutes)
        Arrival time: 200.0 seconds.

    Saves result to a file named 'example.out'


    \033[1m>> detector.py meq.bin meq2.bin -f 50 -np 2 -fir coeffs.txt\033[0m

    Given two seismic signals, 'meq.bin' and 'meq2.txt', sample rate 50 Hz, adds
    background noise of 2.0 dB. Noise is modeled by a FIR filter whose
    coefficients are stored in the file 'coeffs.txt'.


    Results will be saved to 'eq00.out' and 'eq01.out'.
    '''
    try:
        # Setup argument parser
        parser = parse.CustomArgumentParser(description=program_description,
                                            epilog=program_examples,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                fromfile_prefix_chars='@')
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
        parser.set_defaults(func=generate)
        # Create arguments for "generate" command
        parser.add_argument("FILEIN", nargs='*',
                                     action=parse.GlobInputFilenames,
                                     help='''
        Binary or text file containing a seismic-like signal. If not specified
        then a synthetic earthquake is generated.
        ''')
        parser.add_argument("-o", "--output",
                                     default='eq.out',
                                     help='''
        Output file. If none is specified will generate an output file
        for each input file.
        ''')
        parser.add_argument("--output-format",
                                     choices=["binary", "text"],
                                     default="binary",
                                     help='''
        Output file format. Default value is 'binary'.
        ''')
        parser.add_argument("-n", "--n-events",
                                     type=parse.positive_int,
                                     default=1,
                                     help='''
        Number of events generated, one file for each event.
        ''')
        parser.add_argument("-f", "--frequency", type=parse.positive_float,
                                     default=50.0,
                                     dest='fs',
                                     help="Signal frequency.")
        parser.add_argument("-l", "--length",
                                     type=parse.positive_int,
                                     default=600.0,
                                     help='''
        Length of the generated sequence. Default value is 600 seconds.
        ''')
        parser.add_argument("-t", "--t-event",
                                     type=parse.positive_float,
                                     required=True,
                                     help='''
        Point in time at which the event will be generated.
        ''')
        parser.add_argument("-ep", "--earthquake-power",
                                     type=float,
                                     dest='gen_event_power',
                                     default=5.0,
                                     help='''
        Power of the generated seismic event. Default value is 5 dB.
        ''')
        parser.add_argument("-np", "--noise-power",
                                     type=float,
                                     dest='P_noise_db',
                                     default=0.0,
                                     help='''
        Background noise power. Default value is 0 dB.
        ''')
        parser.add_argument("--fir", "--noise-coefficients",
                                     type=parse.filein,
                                     dest='gen_noise_coefficients',
                                     help='''
        Binary or text file containing the coefficients that characterize
        the noise. If not specified then unfiltered white noise is used for
        modeling the background noise.
        ''')
        parser.add_argument("--gen-low-period",
                                     type=parse.positive_float,
                                     dest='low_period',
                                     default=50.0,
                                     help='''
        Initial length of the noise envelope for the different bands.
        Default value is 50.
        ''')
        parser.add_argument("--gen-high-period",
                                     type=parse.positive_float,
                                     dest='high_period',
                                     default=10.0,
                                     help='''
        Final length of the noise envelope for the different bands.
        Default value is 10.
        ''')
        parser.add_argument("--gen-bandwidth",
                                     type=parse.positive_float,
                                     dest='bandwidth',
                                     default=4.0,
                                     help='''
        Channel bandwidth of the filter bank used to generate
        the synthetic earthquake. Default value is 4 Hz.
        ''')
        parser.add_argument("--gen-overlap",
                                     type=parse.positive_float,
                                     dest='overlap',
                                     default=1.0,
                                     help='''
        Overlap of the filter bank used to generate the
        synthetic earthquake. Default value is 1 Hz.
        ''')
        parser.add_argument("--gen-f-low",
                                     type=parse.positive_float,
                                     dest='f_low',
                                     default=2.0,
                                     help='''
        Start frequency of the filter bank used to generate
        the synthetic earthquake. Default value is 2Hz.
        ''')
        parser.add_argument("--gen-f-high",
                                     type=parse.positive_float,
                                     dest='f_high',
                                     default=18.0,
                                     help='''
        End frequency of the filter bank used to generate
        the synthetic earthquake. Default value is 18Hz.
        ''')
        parser.add_argument("--gen-low-amp",
                                     type=parse.positive_float,
                                     dest='low_amp',
                                     default=0.2,
                                     help='''
        Start amplitude of the filter bank used to generate
        the synthetic earthquake. Default value is 0.2.
        ''')
        parser.add_argument("--gen-high-amp",
                                     type=parse.positive_float,
                                     dest='high_amp',
                                     default=0.1,
                                     help='''
        End amplitude of the filter bank used to generate
        the synthetic earthquake. Default value is 0.1.
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
