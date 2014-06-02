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

from setuptools import setup
from setuptools import find_packages
import re


def get_version_number():
    VERSIONFILE = "apasvo/_version.py"
    verstrline = open(VERSIONFILE, "rt").read()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))
    return verstr


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name="APASVO",
      version=get_version_number(),
      description="A graphical tool to perform event detection/picking in seismic traces.",
      author="Jose Emilio Romero Lopez",
      author_email="jemromerol@gmail.com",
      url="https://github.com/jemromerol/apasvo",
      download_url='https://github.com/jemromerol/apasvo/releases/tag/v%s' % get_version_number(),
      license="GPL",
      scripts=["bin/apasvo-detector.py", "bin/apasvo-generator.py", "bin/apasvo-gui.py"],
      install_requires=requirements,
      packages=find_packages(),
      keywords=['seismology', 'earthquakes', 'seismogram', 'picking', 'picker',
                'P-phase arrival', 'STA-LTA', 'AMPA', 'autoregressive method',
                'Takanami', 'characteristic function'],
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering",
                   ],
      )

