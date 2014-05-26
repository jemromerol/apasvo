# -*- mode: python -*-
import sys

a = Analysis(['bin/apasvo-detector.py'],
             pathex=['/apasvo'],
             hiddenimports=['scipy.special._ufuncs_cxx'])

# Added data
data = Tree('./docs', prefix='docs')
data += [('COPYING.txt', 'COPYING.txt', 'DATA'),
                ('README.rst', 'README.rst', 'DATA')]

# Removed data 
a.datas = [x for x in a.datas if not
       x[0].startswith("mpl-data/fonts")]
a.datas = [x for x in a.datas if not
       x[0].startswith("mpl-data/sample_data")]
a.datas = [x for x in a.datas if not
       x[0].startswith("pytz")]

a.binaries = [x for x in a.binaries if not
              x[0].startswith("libnvidia")]
a.binaries = [x for x in a.binaries if not
       x[0].startswith("libQtDeclarative")]
a.binaries = [x for x in a.binaries if not
       x[0].startswith("libQtOpenGL")]
a.binaries = [x for x in a.binaries if not
       x[0].startswith("libQtSQL")]
a.binaries = [x for x in a.binaries if not
       x[0].startswith("wx")]


pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='apasvo-detector%s' % ('.exe' if sys.platform == 'win32' else ''),
          debug=False,
          strip=None,
          upx=True,
          console=True,
          icon='res/images/app.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               data,
               strip=None,
               upx=True,
               name='apasvo-detector')

