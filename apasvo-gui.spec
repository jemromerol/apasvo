# -*- mode: python -*-
a = Analysis(['bin/apasvo-gui.py'],
             pathex=['/apasvo'],
             hiddenimports=['scipy.special._ufuncs_cxx', 'PySide.phonon'],
             hookspath=['hooks'])

# Added data
data = Tree('docs', prefix='docs')
data += [('COPYING.txt', 'COPYING.txt', 'DATA'),
                ('README', 'README', 'DATA'),
                ('README.md', 'README.md', 'DATA')]

# Removed data 
a.datas = [x for x in a.datas if not
           os.path.dirname(x[1]).startswith("C:\\Python27\\lib\site-packages\\matplotlib\\mpl-data\\sample_data")]
a.datas = [x for x in a.datas if not
           os.path.dirname(x[1]).startswith("C:\\Python27\\lib\\site-packages\\matplotlib\\mpl-data\\fonts")]


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

