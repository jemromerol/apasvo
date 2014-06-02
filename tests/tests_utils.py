#!/usr/bin/python2.7
#encoding utf-8

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

import unittest
import numpy as np

from apasvo.utils import plotting


class Check_utils_plotting_reduce_data(unittest.TestCase):

    xdata = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ydata = [5, 0, -5, 0, 1, 2, 0, -1, -2, 5, 5]
    width = 3
    xmin, xmax = 1, 10
    xreduced = [1, 2, 4, 5, 7, 8, 9, 10]
    yreduced = [0, -5, 1, 2, -1, -2, 5, 5]

    def test_reduce_data_returns_correct_results(self):
        xres, yres = plotting.reduce_data(self.xdata, self.ydata, self.width,
                                          self.xmin, self.xmax)
        self.assertTrue(np.all(self.xreduced == xres))
        self.assertTrue(np.all(self.yreduced == yres))

    def test_too_much_width_returns_input_data(self):
        xres, yres = plotting.reduce_data(self.xdata, self.ydata, 15)
        self.assertTrue(np.all(self.xdata == xres))
        self.assertTrue(np.all(self.ydata == yres))

    def test_x_y_with_different_length_returns_error(self):
        self.assertRaises(ValueError, plotting.reduce_data, self.xdata,
                          np.random.randn(5), self.width)

    def test_xmax_not_greater_than_xmin_returns_error(self):
        self.assertRaises(ValueError, plotting.reduce_data, self.xdata,
                          self.ydata, self.width, 6, -5)

if __name__ == "__main__":
    unittest.main()

