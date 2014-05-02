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

import argparse
import os
import glob

from apasvo.utils import futils


def filein(arg):
    """Determines whether an argument is a regular file or not
    (e.g. a directory)."""
    if not os.path.isfile(arg):
        msg = "%r is not a regular file" % arg
        raise argparse.ArgumentTypeError(msg)
    return arg


def positive_float(arg):
    """Checks whether an argument is a positive float number or not."""
    value = float(arg)
    if value <= 0:
        msg = "%r is not a positive float number" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


def positive_int(arg):
    """Checks whether an argument is a positive integer number or not."""
    value = int(arg)
    if value <= 0:
        msg = "%r is not a positive integer number" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


def percentile(arg):
    """Checks if an argument is a valid percentile.

    A correct percentile value must be an integer value in the range 0..100.
    """
    value = float(arg)
    if value < 0 or value > 100:
        msg = "%r is not a percentile" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


def fraction(arg):
    """Determines if an argument is a number in the range [0,1)."""
    value = float(arg)
    if value < 0 or value > 1:
        msg = "%r must be a value between [0,1)" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


class GlobInputFilenames(argparse.Action):
    """Finds all the pathnames according to the specified filename arguments.

    Expands a list of string arguments that represent pathnames. They can be
    either absolute (e.g. /usr/bin/example.txt ) or relative pathnames
    (e.g. ./examples/*.bin).
    Returns a list containing an argparse.FileType object for each filename
    that matches the pattern list.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        fnames = []
        for pname in values:
            if '*' in pname or '?' in pname:
                fnames.extend(glob.glob(pname))
            else:
                fnames.append(pname)
        files = [self._fopen(fname) for fname in fnames]
        setattr(namespace, self.dest, files)

    def _fopen(self, fname):
        if futils.istextfile(fname):
            ft = argparse.FileType('r')
        else:
            ft = argparse.FileType('rb')
        return ft(fname)


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom implementation of ArgumentParser class that supports
    comments in argument files.

    Every sequence of characters preceded by '#' is treated as a comment
    until the end of the line.
    """

    def __init__(self, *args, **kwargs):
        super(CustomArgumentParser, self).__init__(*args, **kwargs)

    def convert_arg_line_to_args(self, line):
        for arg in line.split():
            if not arg.strip():
                continue
            if arg[0] == '#':
                break
            yield arg
