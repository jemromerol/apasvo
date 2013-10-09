'''
Created on 08/10/2013

@author: Jose Emilio Romero Lopez
'''

from setuptools import setup, find_packages

setup(name = "AMPA Command Line Tool",
      version = "0.0.1",
      description = "AMPA Command Line Tool",
      author = "Jose Emilio Romero Lopez",
      author_email = "jemromerol@gmail.com",
      license = "LGPL",
      scripts = ["detector.py", "generator.py"],
      packages = find_packages(),
      install_requires = ['numpy', 'scipy', 'matplotlib']
      )
