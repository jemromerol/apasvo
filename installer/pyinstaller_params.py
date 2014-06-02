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
import os


PATHEX = [os.path.join('.', 'apasvo')]

HIDDEN_IMPORTS = ['scipy.special._ufuncs_cxx', 'PySide.phonon']

HOOKS_PATH = ['hooks']

INCLUDED_DIRS = ['bfirls', 'docs']

INCLUDED_DATA = ['COPYING.txt', 'README.rst']

EXCLUDED_BIN_PREFIXES = ['libnvidia',
                          'libQtDeclarative',
                          'libQtOpenGL',
                          'libQtSql',
                          'libQtNetwork',
                          'libQtSvg',
                          'libQtXml',
                          'libQtScript',
                          'wx']

EXCLUDED_DATA_PREFIXES = [os.path.join('mpl-data', 'fonts'),
                          os.path.join('mpl-data', 'sample_data'),
                          'pytz']
