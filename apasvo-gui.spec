# -*- mode: python -*-

a = Analysis(['bin/apasvo-gui.py'],
             pathex=['/apasvo'],
             hiddenimports=['scipy.special._ufuncs_cxx', 'PySide.phonon'],
             hookspath=['hooks'])

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


a_pyz = PYZ(a.pure)
a_exe = EXE(a_pyz,
            a.scripts + [('O','','OPTION')],
            exclude_binaries=True,
            name='apasvo-gui.exe',
            debug=False,
            strip=None,
            upx=True,
            console=False,
            icon='res/images/app.ico')

coll = COLLECT(a_exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               data,
               strip=None,
               upx=True,
               name='apasvo-gui')

