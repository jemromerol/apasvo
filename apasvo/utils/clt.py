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

import sys
import datetime


def float_secs_2_string_date(x):
    """"""
    times = str(datetime.timedelta(seconds=x)).split('.')
    if len(times) == 1:
        return times[0]
    elif len(times) == 2:
        return "%s.%s" % (times[0], times[1][:-3])
    else:
        raise ValueError("input float value could not be formated")


def print_msg(msg):
    """Prints 'msg' in standard output"""
    sys.stdout.write(msg)
    sys.stdout.flush()


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
            sys.stdout.write("Please respond with "
                             "'yes', 'no', 'all' or 'quit'.\n")


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
        if '&' in answer and not answer.index('&') == len(answer) - 1:
            head, _, tail = answer.partition('&')
            prompt_bits.append(head.lower() + '(' + tail[0].lower() + ')' + tail[1:].lower())
            clean_answer = head + tail
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
            sys.stdout.write("\n" + admonishment + "\n\n\n")


class ALIGN:
    """Use with Column class to specify the alignment mode of a column.

    >>> tb = clt.Table(clt.Column('Column A', [1, 2, 3, 4, 5],
                                  align=clt.ALIGN.LEFT),
                       clt.Column('Column B', [10, 20, 30, 40, 50],
                                  align=clt.ALIGN.RIGHT))
    >>> print tb
     +----------+----------+
     | Column A | Column B |
     +----------+----------+
     | 1        |       10 |
     | 2        |       20 |
     | 3        |       30 |
     | 4        |       40 |
     | 5        |       50 |
     +----------+----------+
    """
    LEFT, RIGHT = '-', ''


class Column():
    """A class that represents a column in a table.

    Use with Table class to draw tables in a CLI.

    Attributes:
        data: List of numeric data stored in the column, where each element
            corresponds to a row in the column.
        name: Header of the column.
        width: Column width in characters.
        format: A specific format string for the elements of 'data'.
            Default format is '%.6g'.
    """

    def __init__(self, name, data, align=ALIGN.RIGHT, fmt='%.6g'):
        self.data = [fmt % x for x in data]
        self.name = name
        self.width = max(len(x) for x in self.data + [name])
        self.format = ' %%%s%ds ' % (align, self.width)


class Table:
    """A class for drawing tabular numeric data in a CLI application.

    >>> tb = clt.Table(clt.Column('Column A', [1, 2, 3, 4, 5]),
                       clt.Column('Column B', [10, 20, 30, 40, 50]))
    >>> print tb
     +----------+----------+
     | Column A | Column B |
     +----------+----------+
     |        1 |       10 |
     |        2 |       20 |
     |        3 |       30 |
     |        4 |       40 |
     |        5 |       50 |
     +----------+----------+

    Attributes:
        columns: A list of column objects corresponding
            to the columns of the table.
        length: Number of rows of the table.
    """

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
    """A class to draw a command line progress bar.

    >>> pbar = clt.ProgressBar(totalWidth=30)
    >>> print pbar
    [             0%             ]
    >>> pbar.updateAmount(40)
    >>> print pbar
    [########### 40%             ]
    >>> pbar.updateAmount(80)
    >>> print pbar
    [############80%#######      ]
    >>> pbar.updateAmount(100)
    >>> print pbar
    [###########100%#############]

    Attributes:
        min: Initial value of the progress. Default value is 0.
        max: Final value of the progress, which corresponds to a complete task.
            Default value is 100.
        span: Length of the range for the progress value. i.e. max - min.
        width: The number of steps of the progress bar.
        amount: A value in the range [min..max] indicating the current progress.
    """

    def __init__(self, minValue=0, maxValue=100, totalWidth=12):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = minValue
        self.max = maxValue
        self.span = maxValue - minValue
        self.width = totalWidth
        self.amount = 0       # When amount == max, we are 100% done
        self.updateAmount(0)  # Build progress bar string

    def updateAmount(self, newAmount=0):
        """Sets the value of the current progress."""
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
