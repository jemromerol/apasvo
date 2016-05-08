######
APASVO
######

*A graphical tool to perform event detection/picking in seismic traces.*



**Main Features**

* Three different picking algorithms available: STA-LTA [1]_, AMPA [2]_ and Takanami's autoregressive method [3]_.
* Proper functionality from DSP tools: scrolling, zooming, panning, playbacking...
* Signal envelope, spectrogram and estimated characteristic function visualization.
* Manually editing of picked seismic events or picking new ones.
* Detect mode: Find all characteristic function's peaks which value is over a threshold value.
* Support for text/binary files containing seismic traces.
* Save picked events to CSV format, and characteristic function to text/binary file format.
* Two additional command line tools: An event picking/detection tool and a synthetic earthquake generator [4]_.

.. contents:: **Table of Contents**
    :local:
    :backlinks: none

============
Installation
============


===========
Screenshots
===========

* http://jemromerol.github.io/media/apasvo-screenshot-1.jpg
* http://jemromerol.github.io/media/apasvo-screenshot-2.jpg
* http://jemromerol.github.io/media/apasvo-screenshot-3.jpg
* http://jemromerol.github.io/media/apasvo-screenshot-4.jpg
* http://jemromerol.github.io/media/apasvo-screenshot-5.jpg
* http://jemromerol.github.io/media/apasvo-screenshot-6.jpg

=======
License
=======

Licensed under the `GPLv3`_ license.

.. _GPLv3: http://www.gnu.org/licenses/gpl-3.0.html

=======
Authors
=======

José Emilio Romero López. jemromerol@gmail.com

==========
References
==========

.. [1] Trnkoczy, A. (2002). Understanding and parameter setting of STA/LTA trigger
   algorithm. IASPEI New Manual of Seismological Observatory Practice, 2, 1-19.
.. [2] Álvarez, I., García, L., Mota, S., Cortés, G., Benítez, C., & De la Torre, A. (2013).
   An Automatic P-Phase Picking Algorithm Based on Adaptive Multiband Processing.
   Geoscience and Remote Sensing Letters, IEEE, Volume: 10, Issue: 6, pp. 1488 - 1492
.. [3] Takanami, T., & Kitagawa, G. (1988).
   A new efficient procedure for the estimation of onset times of seismic waves.
   Journal of Physics of the Earth, 36(6), 267-290.
.. [4] Peterson, Jon. "Observations and modeling of seismic background noise." (1993): 93-95.

=========
Changelog
=========

* 0.0.7 (2016-05-08)
    * Added support to distribute as a conda package.
    * Temporary disable media toolbar in order to support conda
* 0.0.6 (2016-02-07)
    * Add bandpass filtering options
* 0.0.5 (2015-11-30)
    * Add a trace selector window to handle multitrace files. It also allows to open multiple
      files and switch between them.
    * Fix several bugs.
* 0.0.4 (2015-11-09)
    * Refactor apasvo classes to use Obspy library. Thanks to Obspy, now the application supports multiple input
      formats (wav, sac, mseed, segy, ...) besides binary & text, multiple export event formats (NonLinLoc, QuakeML...)
      and (virtually) support for multitrace files.
    * Redesign apasvo-detector to detect events for multitrace files in batch.
    * Fix several bugs
* 0.0.3 (2014-08-16)
    * Fixed several bugs.
* 0.0.2 (2014-06-02)
    * Fixed several bugs.
    * Improve installation files.
* 0.0.1 (2014-05-16)


