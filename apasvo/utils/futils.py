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

import re
import shutil
import os
from struct import pack


# A function that takes an integer in the 8-bit range and returns
# a single-character byte object in py3 / a single-character string
# in py2.
#
_text_characters = (
        b''.join(chr(i) for i in range(32, 127)) +
        b'\n\r\t\f\b')


def istextfile(filename, blocksize=512):
    """ Uses heuristics to guess whether the given file is text or binary,
        by reading a single block of bytes from the file.
        If more than 30% of the chars in the block are non-text, or there
        are NUL ('\x00') bytes in the block, assume this is a binary file.
    """
    with open(filename, 'rb') as fileobj:
        block = fileobj.read(blocksize)
        fileobj.seek(0)
        if b'\x00' in block:
            # Files with null bytes are binary
            return False
        elif not block:
            # An empty file is considered a valid text file
            return True
        # Use translate's 'deletechars' argument to efficiently remove all
        # occurrences of _text_characters from the block
        nontext = block.translate(None, _text_characters)
    return float(len(nontext)) / len(block) <= 0.30


def is_little_endian():
    """Checks whether the current architecture is little-endian or not"""
    if pack('@h', 1) == pack('<h', 1):
        return True
    return False


def read_in_chunks(file_object, chunk_size=1024):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(int(chunk_size))
        if data:
            yield data
        else:
            return


def read_txt_in_chunks(file_object, n=1024, comments='#'):
    """Lazy function (generator) to read a text file in chunks.
    Default chunk size: 1024 characters"""
    numeric_pattern = r'[+-]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?'
    data = []
    for line in file_object.xreadlines():
        line, _, _ = line.partition(comments)  # Eliminate comments
        data.extend(re.findall(numeric_pattern, line))
        if len(data) >= n:
            yield data[:n]
            data = data[n:]
    yield data


def getSize(f):
    """Gets the size of a file in bytes."""
    f.seek(0, 2)  # move the cursor to the end of the file
    size = f.tell()
    f.seek(0)
    return size


def get_delimiter(fileobject, lines=16):
    """Infers the delimiter used in a text file containing a list of numbers.

    The text file must contain on each line a list of numbers separated
    by a delimiter character, e.g.:

    # Example comment
    12.5,10,12
    30,5,3
    3,5,0.5,2.3

    In this case the function will return ',' as delimiter

    Args:
        fileobject: A text file like object.
        lines: The maximum number of lines to be read from the beginning
            of the file in order to detect the delimiter.

    Returns:
        A character corresponding to the delimiter detected.
        An empty string if nothing was found.
    """
    comment = r'\s*#.*'
    integer = r'[+-]?\d+'
    decimal = r'\d+(e[+-]\d+)?'
    number = r'{integer}\.{decimal}'.format(integer=integer, decimal=decimal)
    pattern = (r'{comment}|({number}((?P<sep>[\W]+){number})*({comment})?)'.
               format(number=number, comment=comment))
    delimiters = {}
    for i in xrange(lines):
        line = fileobject.readline()
        if line == '':
            break
        else:
            m = re.match(pattern, line)
            if m:
                delimiter = m.groupdict()['sep']
                if delimiter:
                    if delimiter in delimiters:
                        delimiters[delimiter] += 1
                    else:
                        delimiters[delimiter] = 1
    fileobject.seek(0)
    if delimiters:
        return max(delimiters, key=lambda x: delimiters[x])
    else:
        return ''


def get_sample_rate(filename, max_header_lines=64, comments='#'):
    """Search for a sample rate value in the header of a text file containing
    a seismic signal.

    Args:
        filename: Name of a text file containing a seismic signal.
        max_header_lines: Maximum number of lines to be read from the beginning
            of the file in order to get the sample rate value.
        comments: Character used to indicate the start of a comment

    Returns:
        out: Sample rate, in Hz.
            None if no sample rate value is found in header.
    """
    units = {'hz': 10.0 ** 0, 'khz': 10.0 ** 3,
             'mhz': 10.0 ** 6, 'ghz': 10.0 ** 9}
    pattern = r'sample\s+(rate|frequency).*?(?P<fs>\d+(\.\d*)?(e[+-]?\d+)?).*?(?P<unit>(ghz|mhz|khz|hz))'
    with open(filename, 'r') as f:
        for i in xrange(max_header_lines):
            line = f.readline()
            _, _, comment = line.partition(comments)  # Select comments
            if comment != '':
                m = re.search(pattern, comment.lower())
                if m:
                    fs = m.groupdict()['fs']
                    if fs:
                        return int(float(fs) * units[m.groupdict()['unit']])
    return None


def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy an entire directory tree.
    The destination directory must not already exist.
    """
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
