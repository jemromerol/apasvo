# -*- mode: python -*-
a = Analysis(['bin/detectorgui.py'],
             pathex=['/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx', 'PySide.phonon'],
             hookspath=['./hooks'])

b = Analysis(['bin/detector.py'],
             pathex=['/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx'])

c = Analysis(['bin/generator.py'],
             pathex=['/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx'])

MERGE((a, 'detectorgui', 'bin/detectorgui.py'), (b, 'detector', 'bin/detector.py'), (c, 'generator', 'bin/generator.py'))

data = Tree('./bfirls', prefix='bfirls')
data += Tree('./docs', prefix='docs')
data += [('COPYING.LESSER.txt', 'COPYING.LESSER.txt', 'DATA'),
                ('COPYING.txt', 'COPYING.txt', 'DATA'),
                ('README', 'README', 'DATA'),
                ('README.md', 'README.md', 'DATA'),
                ('options.cfg', 'options.cfg', 'DATA')]

exclude = [('libnvidia-glcore.so.331.20', None, None),
           ('libnvidia-tls.so.331.20', None, None)]


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

a_coll = COLLECT(a_exe,
               a.binaries - exclude,
               a.zipfiles,
               a.datas,
               data,
               strip=None,
               upx=True,
               name='detectorgui')

b_pyz = PYZ(b.pure)

b_exe = EXE(b_pyz,
          b.scripts,
          exclude_binaries=True,
          name='detector.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )

b_coll = COLLECT(b_exe,
               b.binaries,
               b.zipfiles,
               b.datas,
               data,
               strip=None,
               upx=True,
               name='detector')

c_pyz = PYZ(c.pure)

c_exe = EXE(c_pyz,
          c.scripts,
          exclude_binaries=True,
          name='generator.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )

c_coll = COLLECT(c_exe,
               c.binaries,
               c.zipfiles,
               c.datas,
               data,
               strip=None,
               upx=True,
               name='generator')

