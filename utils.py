'''
Created on 09/06/2013

@author: Jose Emilio Romero Lopez
'''
import sys
import re
import numpy as np
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


def read_txt_in_chunks(file_object, n=1024):
    numeric_pattern = r'[+-]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?'
    data = []
    for line in file_object.xreadlines():
        data.extend(re.findall(numeric_pattern, line))
        if len(data) >= n:
            yield data[:n]
            data = data[n:]
    yield data


def getSize(f):
    f.seek(0, 2)  # move the cursor to the end of the file
    size = f.tell()
    f.seek(0)
    return size


def get_delimiter(fileobject, lines=16):
    integer = '[+-]?\d+'
    decimal = '\d+(e[+-]\d+)?'
    number = '{integer}\.{decimal}'.format(integer=integer, decimal=decimal)
    comment = '\s*#.*'
    pattern = ('{comment}|({number}((?P<sep>[\W]+){number})*({comment})?)'.
               format(number=number, comment=comment))
    delimiters = {}
    for i in range(lines):
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


def flatten_dict(d, sep='_'):
    out = {}
    nodes = [(k, v) for k, v in d.iteritems()]
    while nodes:
        (k, v) = nodes.pop()
        if isinstance(v, dict):
            prefix = str(k)
            nodes.extend([("%s%s%s" % (prefix, sep, k), v) for k, v in v.iteritems()])
        else:
            out[k] = v
    return out


def flatten_list(l):
    out = []
    nodes = [v for v in l]
    while nodes:
        v = nodes.pop()
        if isinstance(v, list):
            nodes.extend(v)
        else:
            out.append(v)
    return out[::-1]


def query_yes_no_all_quit(question, default="yes"):
    """Ask a yes/no/all/quit question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no", "all", "quit" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes", "no", "all" or "quit".
    """
    valid = {"yes": "yes",   "y": "yes",    "ye": "yes",
             "no": "no",     "n": "no",
             "all": "all",  "al": "all", "a": "all",
             "quit": "quit", "qui": "quit", "qu": "quit", "q": "quit"}
    if default == None:
        prompt = " [y(yes)/n(no)/a(all)/q(quit)] "
    elif default == "yes":
        prompt = " [Y(Yes)/n(no)/a(all)/q(quit)] "
    elif default == "no":
        prompt = " [y(yes)/N(No)/a(all)/q(quit)] "
    elif default == "all":
        prompt = " [y(yes)/n(no)/A(All)/q(quit)] "
    elif default == "quit":
        prompt = " [y(yes)/n(no)/a(all)/Q(Quit)] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes', 'no', 'all' or 'quit'.\n")


class RawFile(object):

    def __init__(self):
        self.datatypes = {'float16': 'f2', 'float32': 'f4', 'float64': 'f8'}
        self.byteorders = {'little-endian': '<', 'big-endian': '>', 'native': '='}

    def read(self):
        raise NotImplementedError

    def read_in_blocks(self, block_size):
        raise NotImplementedError

    def write(self, array):
        raise NotImplementedError


class BinFile(RawFile):

    def __init__(self, filename, dtype='float64', byteorder='native'):
        super(BinFile, self).__init__()
        self.dtype = np.dtype(self.byteorders[byteorder] + self.datatypes[dtype])
        self.filename = filename

    def read(self):
        return np.fromfile(self.filename, dtype=self.dtype)

    def read_in_blocks(self, block_size=1024):
        with open(self.filename, 'rb') as f:
            chunk_size = block_size * self.dtype.itemsize
            for data in read_in_chunks(f, chunk_size):
                yield np.frombuffer(data, dtype=self.dtype)

    def write(self, array):
        return array.tofile(self.filename)


class TextFile(RawFile):

    def __init__(self, filename, dtype='float64', byteorder='native'):
        super(TextFile, self).__init__()
        self.dtype = np.dtype(self.byteorders[byteorder] + self.datatypes[dtype])
        self.filename = filename

    def read(self, **kwargs):
        return np.loadtxt(self.filename, dtype=self.dtype, **kwargs)

    def read_in_blocks(self, block_size=1024):
        with open(self.filename, 'r') as f:
            for data in read_txt_in_chunks(f, block_size):
                yield np.array(data, dtype=self.dtype)

    def write(self, array, **kwargs):
        return np.savetxt(self.filename, array, **kwargs)


def get_file_handler(filename, fmt='', dtype='float64', byteorder='native', **kwargs):
    if isinstance(filename, file):
        filename = filename.name
    formats = ['binary', 'text']
    if fmt not in formats:
        fmt = 'text' if istextfile(filename) else 'binary'
    if fmt == 'text':
        return TextFile(filename, dtype=dtype, byteorder=byteorder)
    else:
        return BinFile(filename, dtype=dtype, byteorder=byteorder)


def query_custom_answers(question, answers, default=None):
    """Ask a question via raw_input() and return the chosen answer.
    
    @param question {str} Printed on stdout before querying the user.
    @param answers {list} A list of acceptable string answers. Particular
        answers can include '&' before one of its letters to allow a
        single letter to indicate that answer. E.g., ["&yes", "&no",
        "&quit"]. All answer strings should be lowercase.
    @param default {str, optional} A default answer. If no default is
        given, then the user must provide an answer. With a default,
        just hitting <Enter> is sufficient to choose. 
    """
    prompt_bits = []
    answer_from_valid_choice = {
        # <valid-choice>: <answer-without-&>
    }
    clean_answers = []
    for answer in answers:
        if '&' in answer and not answer.index('&') == len(answer)-1:
            head, sep, tail = answer.partition('&')
            prompt_bits.append(head.lower()+'('+tail[0].lower()+')'+tail[1:].lower())
            clean_answer = head+tail
            shortcut = tail[0].lower()
        else:
            prompt_bits.append(answer.lower())
            clean_answer = answer
            shortcut = None
        if default is not None and clean_answer.lower() == default.lower():
            prompt_bits[-1] += " (default)"
        answer_from_valid_choice[clean_answer.lower()] = clean_answer
        if shortcut:
            answer_from_valid_choice[shortcut] = clean_answer
        clean_answers.append(clean_answer.lower())

    # This is what it will look like:
    #   Frob nots the zids? [Yes (default), No, quit] _
    # Possible alternatives:
    #   Frob nots the zids -- Yes, No, quit? [y] _
    #   Frob nots the zids? [*Yes*, No, quit] _
    #   Frob nots the zids? [_Yes_, No, quit] _
    #   Frob nots the zids -- (y)es, (n)o, quit? [y] _
    prompt = " [%s] " % ", ".join(prompt_bits)
    leader = question + prompt
    if len(leader) + max(len(c) for c in answer_from_valid_choice.keys() + ['']) > 78:
        leader = question + '\n' + prompt.lstrip()
    leader = leader.lstrip()

    valid_choices = answer_from_valid_choice.keys()
    if clean_answers:
        admonishment = "*** Please respond with '%s' or '%s'. ***" \
                       % ("', '".join(clean_answers[:-1]), clean_answers[-1])

    while 1:
        sys.stdout.write(leader)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return default
        elif choice in answer_from_valid_choice:
            return answer_from_valid_choice[choice]
        else:
            sys.stdout.write("\n"+admonishment+"\n\n\n")


class ALIGN:
    LEFT, RIGHT = '-', ''


class Column():

    def __init__(self, name, data, align=ALIGN.RIGHT, fmt='%.6g'):
        self.data = [fmt % x for x in data]
        self.name = name
        self.width = max(len(x) for x in self.data + [name])
        self.format = ' %%%s%ds ' % (align, self.width)


class Table:

    def __init__(self, *columns):
        self.columns = columns
        self.length = max(len(column.data) for column in columns)

    def get_row(self, i=None):
        for x in self.columns:
            if i is None:
                yield x.format % x.name
            else:
                yield x.format % x.data[i]

    def get_line(self):
        for x in self.columns:
            yield '-' * (x.width + 2)

    def join_n_wrap(self, char, elements):
        return ' ' + char + char.join(elements) + char

    def get_rows(self):
        yield self.join_n_wrap('+', self.get_line())
        yield self.join_n_wrap('|', self.get_row(None))
        yield self.join_n_wrap('+', self.get_line())
        for i in range(0, self.length):
            yield self.join_n_wrap('|', self.get_row(i))
        yield self.join_n_wrap('+', self.get_line())

    def __str__(self):
        return '\n'.join(self.get_rows())


class ProgressBar:

    def __init__(self, minValue=0, maxValue=10, totalWidth=12):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = minValue
        self.max = maxValue
        self.span = maxValue - minValue
        self.width = totalWidth
        self.amount = 0       # When amount == max, we are 100% done
        self.updateAmount(0)  # Build progress bar string

    def updateAmount(self, newAmount=0):
        if newAmount < self.min:
            newAmount = self.min
        if newAmount > self.max:
            newAmount = self.max
        self.amount = newAmount

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.amount - self.min)
        percentDone = (diffFromMin / float(self.span)) * 100.0
        percentDone = round(percentDone)
        percentDone = int(percentDone)

        # Figure out how many hash bars the percentage should be
        allFull = self.width - 2
        numHashes = (percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # build a progress bar with hashes and spaces
        self.progBar = "[" + '#' * numHashes + ' ' * (allFull - numHashes) + "]"

        # figure out where to put the percentage, roughly centered
        percentPlace = (len(self.progBar) / 2) - len(str(percentDone))
        percentString = str(percentDone) + "%"

        # slice the percentage into the bar
        self.progBar = (self.progBar[0:percentPlace] + percentString +
                        self.progBar[percentPlace + len(percentString):])

    def __str__(self):
        return str(self.progBar)


def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
