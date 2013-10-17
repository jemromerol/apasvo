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

import argparse
import os
import glob

from utils import futils


def filein(arg):
    """"""
    if not os.path.isfile(arg):
        msg = "%r is not a regular file" % arg
        raise argparse.ArgumentTypeError(msg)
    return arg


def positive_float(arg):
    """"""
    value = float(arg)
    if value <= 0:
        msg = "%r is not a positive float number" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


def positive_int(arg):
    """"""
    value = int(arg)
    if value <= 0:
        msg = "%r is not a positive integer number" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


def percentile(arg):
    """"""
    value = float(arg)
    if value < 0 or value > 100:
        msg = "%r is not a percentile" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


def fraction(arg):
    """"""
    value = float(arg)
    if value < 0 or value > 1:
        msg = "%r must be a value between [0,1)" % arg
        raise argparse.ArgumentTypeError(msg)
    return value


def segment_length(arg):
    """"""
    value = float(arg)
    if value < 1 or value > 168:
        msg = "%r must be a value between 1 and 168 hours (one week)" % arg
        raise argparse.ArgumentTypeError(msg)
    return value * 3600


class GlobInputFilenames(argparse.Action):
    """
    """

    def __call__(self, parser, namespace, values, option_string=None):
        """"""
        fnames = []
        for pname in values:
            if '*' in pname or '?' in pname:
                fnames.extend(glob.glob(pname))
            else:
                fnames.append(pname)
        files = [self.fopen(fname) for fname in fnames]
        setattr(namespace, self.dest, files)

    def fopen(self, fname):
        """"""
        if futils.istextfile(fname):
            ft = argparse.FileType('r')
        else:
            ft = argparse.FileType('rb')
        return ft(fname)


class CustomArgumentParser(argparse.ArgumentParser):
    """
    """

    def __init__(self, *args, **kwargs):
        """"""
        super(CustomArgumentParser, self).__init__(*args, **kwargs)

    def convert_arg_line_to_args(self, line):
        """"""
        for arg in line.split():
            if not arg.strip():
                continue
            if arg[0] == '#':
                break
            yield arg
