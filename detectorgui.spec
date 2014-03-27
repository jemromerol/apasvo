# -*- mode: python -*-
a = Analysis(['bin/detectorgui.py'],
             pathex=['/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx', 'PySide.phonon'],
             hookspath=['./hooks'])

data = Tree('./docs', prefix='docs')
data += [('COPYING.LESSER.txt', 'COPYING.LESSER.txt', 'DATA'),
                ('COPYING.txt', 'COPYING.txt', 'DATA'),
                ('README', 'README', 'DATA'),
                ('README.md', 'README.md', 'DATA')]

exclude = [('libnvidia-glcore.so.331.20', None, None),
           ('libnvidia-tls.so.331.20', None, None)]

a.datas = [x for x in a.datas if not
           os.path.dirname(x[1]).startswith("/usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/sample_data")]

a.datas = [x for x in a.datas if not
           os.path.dirname(x[1]).startswith("/usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/sample_data")]

a_pyz = PYZ(a.pure)
a_exe = EXE(a_pyz,
            a.scripts + [('O','','OPTION')],
            exclude_binaries=True,
            name='detectorgui.exe',
            debug=False,
            strip=None,
            upx=True,
            console=True,
            icon='res/images/app.ico')

coll = COLLECT(a_exe,
               a.binaries - exclude,
               a.zipfiles,
               a.datas,
               data,
               strip=None,
               upx=True,
               name='detectorgui')

