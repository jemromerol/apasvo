# -*- mode: python -*-
import sys
import os


# Expand system path to read pyinstaller_params module
sys.path += [os.path.join('.', 'installer')]

import pyinstaller_params


a = Analysis([os.path.join('bin','apasvo-detector.py')],
             pathex=pyinstaller_params.PATHEX,
             hiddenimports=pyinstaller_params.HIDDEN_IMPORTS,
             hookspath=pyinstaller_params.HOOKS_PATH)

# Added data
for dir in pyinstaller_params.INCLUDED_DIRS:
    try:
        data += Tree(os.path.join('.', dir), prefix=dir)
    except:
        data = Tree(os.path.join('.', dir), prefix=dir)

for file in pyinstaller_params.INCLUDED_DATA:
    try:
        data += [(file, file, 'DATA')]
    except:
        data = [(file, file, 'DATA')]

# Removed data 
for prfx in pyinstaller_params.EXCLUDED_DATA_PREFIXES:
    a.datas = [x for x in a.datas if not x[0].startswith(prfx)]

for prfx in pyinstaller_params.EXCLUDED_BIN_PREFIXES:
    a.binaries = [x for x in a.binaries if not x[0].startswith(prfx)]


a_pyz = PYZ(a.pure)
a_exe = EXE(a_pyz,
            a.scripts + [('O','','OPTION')],
            exclude_binaries=True,
            name='apasvo-detector%s' % ('.exe' if sys.platform == 'win32' else ''),
            debug=False,
            strip=None,
            upx=True,
            console=True,
            icon=os.path.join('res', 'images', 'app.ico'))

coll = COLLECT(a_exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               data,
               strip=None,
               upx=True,
               name='apasvo-detector')
