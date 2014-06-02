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

-------
Windows
-------

A prebuilt version of APASVO for Windows is available, compatible with 32-bit and 64-bit machines. You can download it `here`_.

Prebuilt package contains all the required software dependencies to work. Just unzip its contents into a directory of your choice and then you can start using the application.

.. _here: https://github.com/jemromerol/apasvo/releases

-----
Linux
-----

~~~~~~~~~~~~~~~~~
Prebuilt packages
~~~~~~~~~~~~~~~~~

Prebuilt distributions are the recommended installation method because they don't require installing any extra software. Just download the appropriate package for your architecture, unzip its contents into the directory of your choice and you can start using the application.

Prebuilt packages of APASVO for Linux are available for both 32-bit and 64-bit architectures. You can download them `here`_.

.. warning::
   Prebuilt packages for Linux require GLIBC version 2.13 or newer to work. You can check your GLIBC version with:

    ::

    $ ldd --version   


.. _here: https://github.com/jemromerol/apasvo/releases

~~~~~~~~~~~~~~~~~~~~~~
Installation from Pypi
~~~~~~~~~~~~~~~~~~~~~~

*************
Prerequisites
*************

Make sure you have Python 2.7.x installed. Then, install the latest `pip`_ distribution.

*************************************
Installation of required dependencies
*************************************

APASVO depends on a list of Python packages, which you can check in the project's  `requirements.txt`_ file. These packages are automatically installed when APASVO is installed from Python repositories by using ``pip`` or from source code via `setuptools`_.

However, some of these packages, namely Matplotlib and PySide, require installation of a number of additional dependencies. If you're on a Debian / Ubuntu system, you can install these dependencies using the command:

::

$ sudo apt-get build-dep python-pyside python-matplotlib

Or if you are in Fedora/RedHat, first install ``yum-builddep`` and then use the command:

::

$ su -c "yum-builddep python-pyside python-matplotlib"

*******
Install
*******

You can install the latest version of APASVO from Python repositories by using the command:

::

$ pip install --use-wheel apasvo

~~~~~~~~~~~~~~~~~~~~~~~~
Installation from source
~~~~~~~~~~~~~~~~~~~~~~~~

First, make sure you meet the requirements explained in `Prerequisites`_ and install the needed dependencies as explained in `Installation of required dependencies`_ section.

Then, download the latest version from `GitHub`_. If you have ``git`` installed, you can use the following command:

::

$ git clone https://github.com/jemromerol/apasvo.git

Finally, enter the newly created directory containing the source code and run:

::

$ python setup.py install

.. _pip: http://pip.readthedocs.org/en/latest/installing.html
.. _requirements.txt: https://github.com/jemromerol/apasvo/blob/master/requirements.txt
.. _setuptools: https://pythonhosted.org/an_example_pypi_project/setuptools.html#using-setup-py
.. _GitHub: https://github.com/jemromerol/apasvo

----
OS X
----

Sorry, but no precompiled version for OS X is available yet. You can try to install it from Python repositories or from source by following a similar procedure to that described for `Linux`_.

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

* 0.0.2 (2014-06-02)
    * Fixed several bugs.
    * Improve installation files.
* 0.0.1 (2014-05-16)


