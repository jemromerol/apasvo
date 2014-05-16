#-----------------------------------------------------------------------------
# Copyright (c) 2013, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------


hiddenimports = ['sip', 'PySide.QtGui']

from PyInstaller.hooks.hookutils import exec_statement

def qt4_phonon_plugins_dir():
    import os
    qt4_plugin_dirs = eval(exec_statement("from PySide.QtGui import QApplication; app=QApplication([]); app.setApplicationName('pyinstaller'); from PySide.phonon import Phonon; v=Phonon.VideoPlayer(Phonon.VideoCategory); print map(unicode,app.libraryPaths())"))
    if not qt4_plugin_dirs:
        print "E: Cannot find PySide phonon plugin directories"
        return ""
    for d in qt4_plugin_dirs:
        if os.path.isdir(d):
            return str(d)  # must be 8-bit chars for one-file builds
    print "E: Cannot find existing PySide phonon plugin directory"
    return ""

pdir = qt4_phonon_plugins_dir()
datas = [(pdir + "/phonon_backend/*.so", "qt4_plugins/phonon_backend"),
         (pdir + "/phonon_backend/*.dll", "qt4_plugins/phonon_backend"),
         (pdir + "/phonon_backend/*.dylib", "qt4_plugins/phonon_backend")]

# def hook(mod):
#     mod.binaries.extend(qt4_plugins_binaries('phonon_backend'))
#     return mod
