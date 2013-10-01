#!/usr/bin/python2.7
# encoding: utf-8
from distutils.core import setup
import py2exe
import matplotlib

setup(console=['detector.py'],
	  data_files=matplotlib.get_py2exe_datafiles())