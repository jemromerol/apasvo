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


def flatten_dict(d, sep='_'):
    """Flattens a dict.

    E.g. given:

        mdict = {'a': 1, 'b':{'a': 1, 'b': {'a': 1}, 'c': 3}, 'c': 3}

    The output of flatten_dict(mdict) will be:

        {'a': 1, 'b_a': 1, 'b_b_a': 1, 'b_c': 3, 'c': 3}
    """
    out = {}
    nodes = [(k, v) for k, v in d.iteritems()]
    while nodes:
        (k, v) = nodes.pop()
        if isinstance(v, dict):
            prefix = str(k)
            nodes.extend([("%s%s%s" % (prefix, sep, k), v)
                          for k, v in v.iteritems()])
        else:
            out[k] = v
    return out


def flatten_list(l):
    """Flattens a list.

    E.g. given:

        mlist = [1, 2, [[3], [4, 5, [6]], 7, []], 8]

        The output will be [1, 2, 3, 4, 5, 6, 7, 8]
    """
    out = []
    nodes = [v for v in l]
    while nodes:
        v = nodes.pop()
        if isinstance(v, list):
            nodes.extend(v)
        else:
            out.append(v)
    return out[::-1]
